"""Local storage for the web app mockup: SQLite + files under webapp/data (ADR-008 replaces this with Supabase at M6).

Nothing here is engineering data. Projects hold identification only; the YAML design basis stays the source of
project values (ADR-003).
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DATA = Path(os.environ.get("PT_WEBAPP_DATA", Path(__file__).resolve().parents[1] / "data"))
FILES = DATA / "projects"
DB_PATH = DATA / "app.db"
SETTINGS_PATH = DATA / "settings.json"     # holds the API key: local only, git-ignored, never sent to the browser

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL, client TEXT, location TEXT,
  building TEXT, floor TEXT, design_code TEXT NOT NULL, na_mode TEXT NOT NULL, na_country TEXT,
  status TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS files (
  id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL, ext TEXT NOT NULL, kind TEXT NOT NULL, size INTEGER NOT NULL, sha256 TEXT NOT NULL,
  uploaded_at TEXT NOT NULL, status TEXT NOT NULL, message TEXT, info TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  role TEXT NOT NULL, content TEXT NOT NULL, display TEXT NOT NULL, model TEXT, created_at TEXT NOT NULL);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init() -> None:
    with connect() as con:
        con.executescript(SCHEMA)


def rows(sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as con:
        return [dict(r) for r in con.execute(sql, args).fetchall()]


def row(sql: str, args: tuple[Any, ...] = ()) -> Optional[dict[str, Any]]:
    r = rows(sql, args)
    return r[0] if r else None


def execute(sql: str, args: tuple[Any, ...] = ()) -> None:
    with _lock, connect() as con:
        con.execute(sql, args)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def file_dir(project_id: str, file_id: str) -> Path:
    """Each upload gets its own folder, so AutoCAD never sees other files next to it."""
    d = FILES / project_id / file_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def file_out(f: dict[str, Any]) -> dict[str, Any]:
    out = dict(f)
    out["info"] = json.loads(f.get("info") or "{}")
    return out


# --------------------------------------------------------------------------------------------- settings (AI key)
def load_settings() -> dict[str, Any]:
    try:
        data: dict[str, Any] = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_settings(data: dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(SETTINGS_PATH)
