// Browser -> FastAPI (webapp/api). The Claude API key lives only on that server.
export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type NaMode = "UNRESOLVED" | "CEN_RECOMMENDED" | "NA";

export interface Project {
  id: string;
  code: string;
  name: string;
  client: string | null;
  location: string | null;
  building: string | null;
  floor: string | null;
  design_code: string;
  na_mode: NaMode;
  na_country: string | null;
  status: string;
  created_at: string;
  file_count?: number;
}

export interface ProjectFile {
  id: string;
  project_id: string;
  name: string;
  ext: string;
  kind: "drawing" | "drawing-view" | "document" | "table" | "image";
  size: number;
  sha256: string;
  uploaded_at: string;
  status: "processing" | "ready" | "stored" | "failed";
  message: string | null;
  info: Record<string, unknown>;
}

export type Provider = "ollama" | "anthropic";
export interface AIModel { id: string; provider: Provider; label: string; note: string }
export interface AIStatus {
  key_source: "settings" | "environment" | "none";
  key_hint: string | null;
  model: string;
  provider: Provider;
  models: AIModel[];
  last_test: { ok: boolean; model: string; display_name: string; tested_at: string } | null;
  ollama: { running: boolean; version: string | null; models: string[] };
}

/** True when the selected model can be used right now (local model downloaded, or a Claude key saved). */
export function aiReady(s: AIStatus): boolean {
  if (s.provider === "ollama") {
    const name = s.model.replace(/^ollama:/, "");
    return s.ollama.running && (s.ollama.models.includes(name) || s.ollama.models.includes(`${name}:latest`));
  }
  return s.key_source !== "none";
}
export interface Health { ok: boolean; autocad_console: boolean; time: string }
export interface ChatMessage { id: number; role: "user" | "assistant"; display: string; model: string | null; created_at: string }

export class ApiError extends Error {}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, init);
  } catch {
    throw new ApiError("Can't reach the app server on port 8000. Is it running? (start_webapp.bat)");
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = (body as { detail?: unknown }).detail;
    const msg = typeof d === "string" ? d
      : Array.isArray(d) ? d.map((x: { loc?: string[]; msg?: string }) => `${x.loc?.slice(-1)[0] ?? ""}: ${x.msg ?? ""}`).join("; ")
      : `Request failed (${res.status})`;
    throw new ApiError(msg);
  }
  return body as T;
}

const json = (method: string, data: unknown): RequestInit => ({
  method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
});

export const api = {
  health: () => call<Health>("/api/health"),
  aiStatus: () => call<AIStatus>("/api/settings/ai"),
  saveAI: (d: { api_key?: string; model?: string; clear_key?: boolean }) => call<AIStatus>("/api/settings/ai", json("PUT", d)),
  testAI: () => call<{ ok: boolean; model: string; display_name: string }>("/api/settings/ai/test", { method: "POST" }),
  projects: () => call<Project[]>("/api/projects"),
  project: (id: string) => call<Project>(`/api/projects/${id}`),
  createProject: (d: Partial<Project>) => call<Project>("/api/projects", json("POST", d)),
  deleteProject: (id: string) => call<void>(`/api/projects/${id}`, { method: "DELETE" }),
  files: (id: string) => call<ProjectFile[]>(`/api/projects/${id}/files`),
  upload: (id: string, file: File) => {
    const fd = new FormData();
    fd.append("upload", file);
    return call<ProjectFile>(`/api/projects/${id}/files`, { method: "POST", body: fd });
  },
  deleteFile: (pid: string, fid: string) => call<void>(`/api/projects/${pid}/files/${fid}`, { method: "DELETE" }),
  chat: (id: string) => call<ChatMessage[]>(`/api/projects/${id}/chat`),
  send: (id: string, text: string) => call<{ reply: string; model: string }>(`/api/projects/${id}/chat`, json("POST", { text })),
  clearChat: (id: string) => call<void>(`/api/projects/${id}/chat`, { method: "DELETE" }),
  contentUrl: (pid: string, fid: string) => `${API}/api/projects/${pid}/files/${fid}/content`,
  previewUrl: (pid: string, fid: string) => `${API}/api/projects/${pid}/files/${fid}/preview`,
};

export const ACCEPT = ".dxf,.dwg,.dwf,.dwfx,.pdf,.xlsx,.xls,.csv,.png,.jpg,.jpeg";

export function bytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export const NA_LABEL: Record<NaMode, string> = {
  UNRESOLVED: "National Annex not decided",
  CEN_RECOMMENDED: "CEN recommended values",
  NA: "National Annex",
};
