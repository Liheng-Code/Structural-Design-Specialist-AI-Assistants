"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api, NA_LABEL, type NaMode, type Project } from "@/lib/api";

function NewProject({ onCancel }: { onCancel: () => void }) {
  const router = useRouter();
  const [f, setF] = useState({ code: "", name: "", client: "", location: "", building: "", floor: "", na_mode: "UNRESOLVED" as NaMode, na_country: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const blank = (v: string) => (v.trim() ? v.trim() : null);
      const p = await api.createProject({
        code: f.code, name: f.name, client: blank(f.client), location: blank(f.location), building: blank(f.building),
        floor: blank(f.floor), na_mode: f.na_mode, na_country: f.na_mode === "NA" ? blank(f.na_country) : null,
      });
      router.push(`/projects/${p.id}`);
    } catch (e2) {
      setErr((e2 as Error).message);
      setBusy(false);
    }
  }

  const input = (k: keyof typeof f, label: string, ph: string, req = false) => (
    <label className="grid gap-1.5">
      <span className="text-sm font-medium">{label}{req && <span className="text-bad"> *</span>}</span>
      <input id={`np-${k}`} className="field" placeholder={ph} value={f[k]} onChange={set(k)} required={req} />
    </label>
  );

  return (
    <form onSubmit={submit} className="panel grid gap-5 p-5">
      <div className="flex items-baseline justify-between">
        <h2 className="font-display text-2xl font-semibold">New project</h2>
        <span className="label">Design code: Eurocodes</span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {input("code", "Project code", "e.g. PJR-2F-PT", true)}
        {input("name", "Project name", "e.g. Warehouse 2F PT slab", true)}
        {input("client", "Client", "optional")}
        {input("location", "Location", "optional")}
        {input("building", "Building", "optional")}
        {input("floor", "Floor / level", "e.g. 2F")}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="text-sm font-medium">National Annex</span>
          <select id="np-na" className="field" value={f.na_mode} onChange={set("na_mode")}>
            <option value="UNRESOLVED">Not decided yet</option>
            <option value="CEN_RECOMMENDED">CEN recommended values (no NA)</option>
            <option value="NA">Use a National Annex</option>
          </select>
          <span className="text-xs text-ink2">Until this is decided, code checks report NOT EVALUATED.</span>
        </label>
        {f.na_mode === "NA" && input("na_country", "NA country", "e.g. United Kingdom", true)}
      </div>
      {err && <p role="alert" className="rounded-sm bg-badsoft px-3 py-2 text-sm text-bad">{err}</p>}
      <div className="flex gap-3">
        <button className="btn-primary" disabled={busy}>{busy ? "Creating…" : "Create project"}</button>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

function ProjectsInner() {
  const params = useSearchParams();
  const [showNew, setShowNew] = useState(params.get("new") === "1");
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.projects().then(setProjects, (e: Error) => setErr(e.message));
  }, []);

  return (
    <div className="grid gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b-2 border-ink pb-4">
        <div className="grid gap-1">
          <p className="label">Workspace</p>
          <h1 className="font-display text-4xl font-bold">Projects</h1>
        </div>
        {!showNew && <button className="btn-primary" onClick={() => setShowNew(true)}>New project</button>}
      </header>

      {showNew && <NewProject onCancel={() => setShowNew(false)} />}
      {err && <p className="rounded-sm bg-badsoft px-3 py-2 text-sm text-bad">{err}</p>}

      {projects && projects.length === 0 && !showNew && (
        <div className="panel grid justify-items-start gap-3 p-8">
          <h2 className="font-display text-2xl font-semibold">No projects yet</h2>
          <p className="text-ink2">Create one to start importing drawings and talking to Claude about it.</p>
          <button className="btn-primary" onClick={() => setShowNew(true)}>New project</button>
        </div>
      )}

      {projects && projects.length > 0 && (
        <div className="overflow-x-auto border border-rule2">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="bg-accentsoft text-left">
              <tr>{["Code", "Name", "Client", "Floor", "Code basis", "Files", "Status"].map((h) => <th key={h} className="label px-3 py-2 font-medium">{h}</th>)}</tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id} className="border-t border-rule hover:bg-paper">
                  <td className="px-3 py-2.5 font-mono"><Link className="text-accent hover:underline" href={`/projects/${p.id}`}>{p.code}</Link></td>
                  <td className="px-3 py-2.5 font-medium">{p.name}</td>
                  <td className="px-3 py-2.5 text-ink2">{p.client ?? "–"}</td>
                  <td className="px-3 py-2.5 text-ink2">{p.floor ?? "–"}</td>
                  <td className="px-3 py-2.5 text-ink2">{NA_LABEL[p.na_mode]}{p.na_country ? ` (${p.na_country})` : ""}</td>
                  <td className="px-3 py-2.5 tabular-nums">{p.file_count ?? 0}</td>
                  <td className="px-3 py-2.5"><span className="rounded-sm bg-paper px-2 py-0.5 font-mono text-[11px]">{p.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function Projects() {
  return <Suspense><ProjectsInner /></Suspense>;
}
