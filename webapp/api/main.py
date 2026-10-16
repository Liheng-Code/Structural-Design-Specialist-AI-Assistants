"""PT Designer web app API (mockup slice of M6; ADR-005). Run: python -m uvicorn main:app --port 8000 (from webapp/api).

Local only: binds to 127.0.0.1, stores data in webapp/data, no sign-in yet (roles arrive with Supabase Auth, ADR-008).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

import ai
import files as fx
import store

app = FastAPI(title="PT Designer API", version="0.1.0")
# The browser app on localhost:3000 calls this API directly (large uploads, long Claude replies).
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                   allow_methods=["*"], allow_headers=["*"])
store.init()


@app.exception_handler(ai.AIError)
def _ai_error(_: Any, exc: ai.AIError) -> JSONResponse:
    return JSONResponse({"detail": exc.message}, status_code=exc.status)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "autocad_console": bool(fx.accoreconsole()), "time": store.now()}


# --------------------------------------------------------------------------------------------- AI settings
class AISettingsIn(BaseModel):
    api_key: Optional[str] = Field(default=None, max_length=400)
    model: Optional[str] = None
    clear_key: bool = False


@app.get("/api/settings/ai")
def get_ai() -> dict[str, Any]:
    return ai.status()


@app.put("/api/settings/ai")
def put_ai(body: AISettingsIn) -> dict[str, Any]:
    s = store.load_settings()
    if body.clear_key:
        s.pop("api_key", None)
        s.pop("last_test", None)
    if body.api_key:
        key = body.api_key.strip()
        if not key.startswith("sk-ant-"):
            raise HTTPException(400, "That doesn't look like an Anthropic API key (they start with sk-ant-).")
        s["api_key"] = key
        s.pop("last_test", None)
    if body.model:
        if body.model not in {m["id"] for m in ai.MODELS}:
            raise HTTPException(400, f"Unknown model {body.model}")
        s["model"] = body.model
    store.save_settings(s)
    return ai.status()


@app.post("/api/settings/ai/test")
def test_ai() -> dict[str, Any]:
    return ai.test_connection(ai.status()["model"])


# --------------------------------------------------------------------------------------------- projects
class ProjectIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=200)
    client: Optional[str] = Field(default=None, max_length=200)
    location: Optional[str] = Field(default=None, max_length=200)
    building: Optional[str] = Field(default=None, max_length=100)
    floor: Optional[str] = Field(default=None, max_length=100)
    design_code: Literal["Eurocodes"] = "Eurocodes"
    na_mode: Literal["UNRESOLVED", "CEN_RECOMMENDED", "NA"] = "UNRESOLVED"
    na_country: Optional[str] = Field(default=None, max_length=100)

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]*", v):
            raise ValueError("use letters, digits, dot, dash or underscore")
        return v


def _project(pid: str) -> dict[str, Any]:
    p = store.row("SELECT * FROM projects WHERE id = ?", (pid,))
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@app.get("/api/projects")
def list_projects() -> list[dict[str, Any]]:
    return store.rows("""SELECT p.*, (SELECT COUNT(*) FROM files f WHERE f.project_id = p.id) AS file_count
                         FROM projects p ORDER BY created_at DESC""")


@app.post("/api/projects", status_code=201)
def create_project(body: ProjectIn) -> dict[str, Any]:
    if body.na_mode == "NA" and not body.na_country:
        raise HTTPException(400, "Give the National Annex country, or choose CEN recommended / not decided yet")
    if store.row("SELECT id FROM projects WHERE code = ?", (body.code,)):
        raise HTTPException(409, f"A project with code {body.code} already exists")
    pid = store.new_id()
    store.execute("""INSERT INTO projects (id, code, name, client, location, building, floor, design_code, na_mode,
                     na_country, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (pid, body.code, body.name.strip(), body.client, body.location, body.building, body.floor,
                   body.design_code, body.na_mode, body.na_country, "Draft", store.now()))
    return _project(pid)


@app.get("/api/projects/{pid}")
def get_project(pid: str) -> dict[str, Any]:
    return _project(pid)


@app.delete("/api/projects/{pid}", status_code=204)
def delete_project(pid: str) -> None:
    import shutil
    p = _project(pid)
    store.execute("DELETE FROM projects WHERE id = ?", (p["id"],))   # files and messages cascade
    shutil.rmtree(store.FILES / p["id"], ignore_errors=True)


# --------------------------------------------------------------------------------------------- files
def _file(pid: str, fid: str) -> dict[str, Any]:
    f = store.row("SELECT * FROM files WHERE id = ? AND project_id = ?", (fid, pid))
    if not f:
        raise HTTPException(404, "File not found")
    return f


def _stored_path(pid: str, f: dict[str, Any]) -> Path:
    return store.file_dir(pid, f["id"]) / f"original{f['ext']}"


def _process(pid: str, fid: str) -> None:
    f = store.row("SELECT * FROM files WHERE id = ?", (fid,))
    if not f:
        return
    status, message, info = fx.process(_stored_path(pid, f), f["ext"])
    store.execute("UPDATE files SET status = ?, message = ?, info = ? WHERE id = ?",
                  (status, message, json.dumps(info), fid))


@app.get("/api/projects/{pid}/files")
def list_files(pid: str) -> list[dict[str, Any]]:
    _project(pid)
    return [store.file_out(f) for f in
            store.rows("SELECT * FROM files WHERE project_id = ? ORDER BY uploaded_at DESC", (pid,))]


@app.post("/api/projects/{pid}/files", status_code=201)
async def upload(pid: str, background: BackgroundTasks, upload: UploadFile = File(...)) -> dict[str, Any]:
    _project(pid)
    name = Path(upload.filename or "upload").name[:200]
    ext = Path(name).suffix.lower()
    if ext not in fx.KINDS:
        raise HTTPException(415, f"{ext or 'no extension'} isn't supported. Use: {', '.join(sorted(fx.KINDS))}")
    fid = store.new_id()
    dest = store.file_dir(pid, fid) / f"original{ext}"
    h, size = hashlib.sha256(), 0
    with open(dest, "wb") as out:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > fx.MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(413, "File is larger than 200 MB")
            h.update(chunk)
            out.write(chunk)
    store.execute("""INSERT INTO files (id, project_id, name, ext, kind, size, sha256, uploaded_at, status, message)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  (fid, pid, name, ext, fx.KINDS[ext], size, h.hexdigest(), store.now(), "processing",
                   "Converting with AutoCAD…" if ext == ".dwg" else "Reading file…"))
    background.add_task(_process, pid, fid)
    return store.file_out(_file(pid, fid))


@app.get("/api/projects/{pid}/files/{fid}/content")
def file_content(pid: str, fid: str) -> FileResponse:
    f = _file(pid, fid)
    media = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    inline = f["ext"] in media
    return FileResponse(_stored_path(pid, f), media_type=media.get(f["ext"], "application/octet-stream"),
                        filename=f["name"], content_disposition_type="inline" if inline else "attachment")


@app.get("/api/projects/{pid}/files/{fid}/preview")
def file_preview(pid: str, fid: str) -> FileResponse:
    f = _file(pid, fid)
    svg = store.file_dir(pid, f["id"]) / "preview.svg"
    if not svg.is_file():
        raise HTTPException(404, "No preview for this file")
    return FileResponse(svg, media_type="image/svg+xml")


@app.delete("/api/projects/{pid}/files/{fid}", status_code=204)
def delete_file(pid: str, fid: str) -> None:
    f = _file(pid, fid)
    store.execute("DELETE FROM files WHERE id = ?", (f["id"],))
    d = store.file_dir(pid, f["id"])
    for p in d.iterdir():
        p.unlink()
    d.rmdir()


# --------------------------------------------------------------------------------------------- assistant
class ChatIn(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


@app.get("/api/projects/{pid}/chat")
def chat_history(pid: str) -> list[dict[str, Any]]:
    _project(pid)
    return store.rows("SELECT id, role, display, model, created_at FROM messages WHERE project_id = ? ORDER BY id",
                      (pid,))


@app.post("/api/projects/{pid}/chat")
def chat(pid: str, body: ChatIn) -> dict[str, Any]:
    p = _project(pid)
    flist = store.rows("SELECT * FROM files WHERE project_id = ? ORDER BY uploaded_at", (pid,))
    history = store.rows("SELECT role, content FROM messages WHERE project_id = ? ORDER BY id", (pid,))
    out = ai.chat(p, flist, history, body.text)
    t = store.now()
    store.execute("INSERT INTO messages (project_id, role, content, display, model, created_at) VALUES (?,?,?,?,?,?)",
                  (pid, "user", json.dumps(out["user_content"]), body.text, None, t))
    store.execute("INSERT INTO messages (project_id, role, content, display, model, created_at) VALUES (?,?,?,?,?,?)",
                  (pid, "assistant", json.dumps(out["assistant_content"]), out["reply"], out["model"], store.now()))
    return {"reply": out["reply"], "model": out["model"], "usage": out["usage"]}


@app.delete("/api/projects/{pid}/chat", status_code=204)
def clear_chat(pid: str) -> None:
    _project(pid)
    store.execute("DELETE FROM messages WHERE project_id = ?", (pid,))
