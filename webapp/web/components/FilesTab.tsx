"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ACCEPT, api, bytes, type ProjectFile } from "@/lib/api";

const STATUS: Record<ProjectFile["status"], string> = {
  processing: "bg-accentsoft text-accent",
  ready: "bg-oksoft text-ok",
  stored: "bg-warnsoft text-warn",
  failed: "bg-badsoft text-bad",
};
const STATUS_LABEL: Record<ProjectFile["status"], string> = {
  processing: "working", ready: "read", stored: "stored only", failed: "failed",
};

function Viewer({ f }: { f: ProjectFile }) {
  const [zoom, setZoom] = useState(1);
  const info = f.info as Record<string, unknown>;
  const hasPreview = f.status === "ready" && (f.ext === ".dxf" || f.ext === ".dwg");
  const layers = (info.layers as string[] | undefined) ?? [];
  const entities = (info.entities as Record<string, number> | undefined) ?? {};

  useEffect(() => {
    setZoom(1);
  }, [f.id]);

  return (
    <div className="panel grid min-w-0 content-start gap-4 p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="min-w-0 break-all font-display text-xl font-semibold">{f.name}</h3>
        <a href={api.contentUrl(f.project_id, f.id)} className="text-sm text-accent hover:underline" target="_blank" rel="noreferrer">
          {f.ext === ".pdf" || f.kind === "image" ? "Open" : "Download"} original
        </a>
      </div>
      <p className={`rounded-sm px-3 py-2 text-sm ${STATUS[f.status]}`}>{f.message}</p>

      {hasPreview && (
        <div className="grid gap-2">
          <div className="flex items-center gap-2">
            <span className="label mr-auto">Preview (rendered from DXF, black on white)</span>
            <button className="btn-ghost px-2 py-1" onClick={() => setZoom((z) => Math.max(0.5, z / 1.5))} aria-label="Zoom out">−</button>
            <span className="w-12 text-center font-mono text-xs tabular-nums">{Math.round(zoom * 100)}%</span>
            <button className="btn-ghost px-2 py-1" onClick={() => setZoom((z) => Math.min(8, z * 1.5))} aria-label="Zoom in">+</button>
          </div>
          <div className="h-[420px] overflow-auto border border-rule bg-white">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={api.previewUrl(f.project_id, f.id)} alt={`Drawing preview of ${f.name}`} style={{ width: `${zoom * 100}%`, maxWidth: "none" }} />
          </div>
        </div>
      )}
      {f.status === "ready" && f.ext === ".pdf" && (
        <iframe title={f.name} src={api.contentUrl(f.project_id, f.id)} className="h-[520px] w-full border border-rule bg-white" />
      )}
      {f.status === "ready" && f.kind === "image" && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={api.contentUrl(f.project_id, f.id)} alt={f.name} className="max-h-[520px] border border-rule object-contain" />
      )}

      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
        <dt className="text-ink2">Size</dt><dd className="tabular-nums">{bytes(f.size)}</dd>
        <dt className="text-ink2">Uploaded</dt><dd>{new Date(f.uploaded_at).toLocaleString()}</dd>
        {"dwg_version" in info && (<><dt className="text-ink2">DWG version</dt><dd>{String(info.dwg_version)}</dd></>)}
        {"dxf_version" in info && (<><dt className="text-ink2">DXF version</dt><dd className="font-mono">{String(info.dxf_version)}</dd></>)}
        {"units" in info && (<><dt className="text-ink2">Drawing units</dt><dd className={info.units === "unitless" ? "text-warn" : ""}>{String(info.units)}{info.units === "unitless" ? " (not set in the file)" : ""}</dd></>)}
        {"pages" in info && (<><dt className="text-ink2">Pages</dt><dd className="tabular-nums">{String(info.pages)}</dd></>)}
        {"page_size_mm" in info && (<><dt className="text-ink2">Page size</dt><dd className="tabular-nums">{(info.page_size_mm as number[]).join(" × ")} mm</dd></>)}
        <dt className="text-ink2">SHA-256</dt><dd className="break-all font-mono text-xs">{f.sha256}</dd>
      </dl>

      {layers.length > 0 && (
        <details className="grid gap-2">
          <summary className="cursor-pointer text-sm font-medium">{layers.length} layers · {Object.values(entities).reduce((a, b) => a + b, 0)} entities</summary>
          <div className="mt-2 grid gap-3 sm:grid-cols-2">
            <ul className="max-h-56 overflow-auto border border-rule p-2 font-mono text-xs">{layers.map((l) => <li key={l}>{l}</li>)}</ul>
            <table className="h-fit text-xs">
              <tbody>{Object.entries(entities).map(([k, n]) => (
                <tr key={k} className="border-b border-rule"><td className="py-1 pr-4 font-mono">{k}</td><td className="py-1 text-right tabular-nums">{n}</td></tr>
              ))}</tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}

export default function FilesTab({ projectId }: { projectId: string }) {
  const [files, setFiles] = useState<ProjectFile[] | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState<string[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const input = useRef<HTMLInputElement>(null);

  const load = useCallback(() => api.files(projectId).then((fl) => {
    setFiles(fl);
    setSel((s) => s ?? fl[0]?.id ?? null);
    return fl;
  }), [projectId]);

  useEffect(() => { load().catch((e: Error) => setErrors([e.message])); }, [load]);

  // Poll while anything is still being read or converted.
  useEffect(() => {
    if (!files?.some((f) => f.status === "processing")) return;
    const t = setTimeout(() => { load().catch(() => undefined); }, 1500);
    return () => clearTimeout(t);
  }, [files, load]);

  async function add(list: FileList | null) {
    if (!list?.length) return;
    setErrors([]);
    for (const file of Array.from(list)) {
      setUploading((u) => [...u, file.name]);
      try {
        const f = await api.upload(projectId, file);
        setSel(f.id);
      } catch (e) {
        setErrors((x) => [...x, `${file.name}: ${(e as Error).message}`]);
      } finally {
        setUploading((u) => u.filter((n) => n !== file.name));
      }
      await load();
    }
  }

  async function remove(f: ProjectFile) {
    await api.deleteFile(projectId, f.id);
    setSel(null);
    await load();
  }

  const selected = files?.find((f) => f.id === sel) ?? null;

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
      <div className="grid content-start gap-4">
        <div
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); add(e.dataTransfer.files); }}
          className={`grid justify-items-center gap-2 border-2 border-dashed p-6 text-center ${drag ? "border-accent bg-accentsoft" : "border-rule2 bg-sheet"}`}
        >
          <p className="font-display text-xl font-semibold">Drop drawings here</p>
          <p className="text-sm text-ink2">DWG, DXF, DWF, DWFX, PDF, XLSX/CSV, PNG/JPG · up to 200 MB</p>
          <input ref={input} id="file-input" type="file" multiple accept={ACCEPT} className="hidden" onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
          <button className="btn-primary mt-1" onClick={() => input.current?.click()}>Choose files</button>
        </div>
        {uploading.map((n) => <p key={n} className="text-sm text-accent">Uploading {n}…</p>)}
        {errors.map((m) => <p key={m} role="alert" className="rounded-sm bg-badsoft px-3 py-2 text-sm text-bad">{m}</p>)}

        <div className="grid gap-1">
          <p className="label">{files ? `${files.length} file(s)` : "Loading…"}</p>
          {files?.length === 0 && <p className="text-sm text-ink2">No files yet. Start with the structural layout as DWG or DXF.</p>}
          <ul className="grid gap-1.5">
            {files?.map((f) => (
              <li key={f.id}>
                <div className={`flex items-start gap-2 border px-3 py-2 ${f.id === sel ? "border-ink bg-sheet" : "border-rule bg-sheet/60 hover:border-rule2"}`}>
                  <button className="grid min-w-0 flex-1 text-left" onClick={() => setSel(f.id)}>
                    <span className="flex items-center gap-2">
                      <span className="font-mono text-[11px] uppercase text-ink2">{f.ext.slice(1)}</span>
                      <span className="truncate text-sm font-medium">{f.name}</span>
                    </span>
                    <span className="text-xs text-ink2 tabular-nums">{bytes(f.size)}</span>
                  </button>
                  <span className={`shrink-0 rounded-sm px-1.5 py-0.5 font-mono text-[10.5px] ${STATUS[f.status]}`}>{STATUS_LABEL[f.status]}</span>
                  <button className="shrink-0 px-1 text-xs text-ink2 hover:text-bad" onClick={() => remove(f)} aria-label={`Remove ${f.name}`}>✕</button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {selected ? <Viewer f={selected} /> : (
        <div className="panel grid place-items-center p-10 text-sm text-ink2">Select a file to see what was read from it.</div>
      )}
    </div>
  );
}
