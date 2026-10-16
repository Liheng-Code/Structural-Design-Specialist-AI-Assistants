"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { api, NA_LABEL, type Project } from "@/lib/api";
import FilesTab from "@/components/FilesTab";
import AssistantTab from "@/components/AssistantTab";

const TABS = [
  { id: "files", label: "Files", live: true },
  { id: "assistant", label: "Assistant", live: true },
  { id: "geometry", label: "Geometry", live: false, ms: "M5" },
  { id: "analysis", label: "Analysis", live: false, ms: "M1" },
  { id: "pt", label: "PT design", live: false, ms: "M2" },
  { id: "drawings", label: "Drawings & reports", live: false, ms: "M4" },
] as const;

export default function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [p, setP] = useState<Project | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<string>("files");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const router = useRouter();

  async function remove() {
    try {
      await api.deleteProject(id);
      router.push("/projects");
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  useEffect(() => {
    api.project(id).then(setP, (e: Error) => setErr(e.message));
  }, [id]);

  if (err) return <p className="rounded-sm bg-badsoft px-3 py-2 text-sm text-bad">{err} <Link href="/projects" className="underline">Back to projects</Link></p>;
  if (!p) return <p className="text-ink2">Loading project…</p>;

  const facts: [string, string | null][] = [
    ["Client", p.client], ["Location", p.location], ["Building", p.building], ["Floor", p.floor],
    ["Code basis", `${p.design_code} · ${NA_LABEL[p.na_mode]}${p.na_country ? ` (${p.na_country})` : ""}`],
  ];

  return (
    <div className="grid gap-5">
      <header className="grid gap-3 border-b-2 border-ink pb-4">
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/projects" className="label hover:text-ink">Projects /</Link>
          <span className="font-mono text-sm">{p.code}</span>
          <span className="rounded-sm bg-paper px-2 py-0.5 font-mono text-[11px] ring-1 ring-rule2">{p.status}</span>
          <div className="ml-auto flex items-center gap-2">
            {confirmDelete ? (
              <>
                <span className="text-sm text-bad">Delete this project and all its files?</span>
                <button className="btn-ghost px-2.5 py-1 text-xs text-bad" onClick={remove}>Delete</button>
                <button className="btn-ghost px-2.5 py-1 text-xs" onClick={() => setConfirmDelete(false)}>Keep</button>
              </>
            ) : (
              <button className="px-1 text-xs text-ink2 hover:text-bad" onClick={() => setConfirmDelete(true)}>Delete project</button>
            )}
          </div>
        </div>
        <h1 className="font-display text-4xl font-bold">{p.name}</h1>
        <dl className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
          {facts.filter(([, v]) => v).map(([k, v]) => (
            <div key={k} className="flex gap-1.5"><dt className="text-ink2">{k}</dt><dd className="font-medium">{v}</dd></div>
          ))}
        </dl>
        {p.na_mode === "UNRESOLVED" && (
          <p className="text-sm text-warn">National Annex not decided: code checks will report NOT EVALUATED until it is.</p>
        )}
      </header>

      <div role="tablist" aria-label="Project sections" className="flex flex-wrap gap-1 border-b border-rule2">
        {TABS.map((t) => (
          <button
            key={t.id}
            id={`tab-${t.id}`}
            role="tab"
            aria-selected={tab === t.id}
            disabled={!t.live}
            title={t.live ? undefined : `Arrives at milestone ${"ms" in t ? t.ms : ""}`}
            onClick={() => setTab(t.id)}
            className={`-mb-px flex items-center gap-2 border-b-2 px-3 py-2 text-sm ${tab === t.id ? "border-ink font-semibold" : "border-transparent text-ink2 hover:text-ink"} disabled:cursor-not-allowed disabled:text-ink2/50`}
          >
            {t.label}
            {!t.live && "ms" in t && <span className="font-mono text-[10px] text-ink2/70">{t.ms}</span>}
          </button>
        ))}
      </div>

      {tab === "files" && <FilesTab projectId={p.id} />}
      {tab === "assistant" && <AssistantTab projectId={p.id} />}
    </div>
  );
}
