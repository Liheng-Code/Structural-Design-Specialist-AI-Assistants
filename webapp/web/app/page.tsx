"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { aiReady, api, NA_LABEL, type AIStatus, type Health, type Project } from "@/lib/api";

const ROADMAP = [
  { id: "Now", name: "Workspace", text: "Projects, drawing import, DWG conversion, AI assistant", live: true },
  { id: "M1", name: "SAFE / ETABS import", text: "Analysis results read from your exports", live: false },
  { id: "M2", name: "PT calculations", text: "Losses, stresses, ULS, punching", live: false },
  { id: "M3", name: "Design loop", text: "Tendons, iteration, reinforcement", live: false },
  { id: "M4", name: "Deliverables", text: "Drawings, calc report, schedules", live: false },
];

function Step({ n, title, done, children, href, cta }: {
  n: number; title: string; done: boolean; children: React.ReactNode; href: string; cta: string;
}) {
  return (
    <div className="panel flex flex-col gap-3 p-5">
      <div className="flex items-center justify-between">
        <span className="font-display text-3xl font-bold text-accent">{n}</span>
        <span className={`rounded-sm px-2 py-0.5 font-mono text-[11px] ${done ? "bg-oksoft text-ok" : "bg-paper text-ink2"}`}>
          {done ? "done" : "to do"}
        </span>
      </div>
      <h3 className="font-display text-xl font-semibold">{title}</h3>
      <div className="text-sm text-ink2">{children}</div>
      <Link href={href} className="btn-ghost mt-auto self-start">{cta}</Link>
    </div>
  );
}

export default function Home() {
  const [ai, setAi] = useState<AIStatus | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [offline, setOffline] = useState<string | null>(null);

  useEffect(() => {
    api.health().then(setHealth, (e: Error) => setOffline(e.message));
    api.aiStatus().then(setAi, () => undefined);
    api.projects().then(setProjects, () => undefined);
  }, []);

  const aiDone = !!ai && aiReady(ai);
  const aiLabel = ai?.models.find((m) => m.id === ai.model)?.label ?? ai?.model;
  const hasProject = !!projects?.length;
  const hasFiles = !!projects?.some((p) => (p.file_count ?? 0) > 0);

  return (
    <div className="grid gap-10">
      <section className="grid gap-6 border-b-2 border-ink pb-8 pt-4 lg:grid-cols-[1.4fr_1fr] lg:items-end">
        <div className="grid gap-4">
          <p className="label">Eurocode · bonded post-tensioning · local workspace</p>
          <h1 className="font-display text-5xl font-bold leading-[1.02] sm:text-6xl">
            From the structural layout to a checked PT design package.
          </h1>
          <p className="max-w-[60ch] text-lg text-ink2">
            Set up a project, bring in the drawings you already have, and work with an AI assistant on them, free on this PC or Claude when you need more. Calculations,
            drawings and reports are added milestone by milestone, and each one is checked before it goes live.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/projects?new=1" className="btn-primary">Create a project</Link>
            <Link href="/settings" className="btn-ghost">Set up AI</Link>
          </div>
        </div>
        <div className="panel grid gap-3 p-5">
          <p className="label">This PC</p>
          {offline ? (
            <p className="text-sm text-bad">{offline}</p>
          ) : (
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
              <dt className="text-ink2">App server</dt>
              <dd>{health ? <span className="text-ok">running</span> : "…"}</dd>
              <dt className="text-ink2">DWG conversion</dt>
              <dd>{health ? (health.autocad_console ? <span className="text-ok">AutoCAD console found</span> : <span className="text-warn">not available; upload DXF</span>) : "…"}</dd>
              <dt className="text-ink2">AI model</dt>
              <dd>{ai ? (aiDone ? <span className="text-ok">{aiLabel} ready{ai.provider === "ollama" ? " (free, local)" : ""}</span> : <span className="text-warn">{aiLabel}: not ready</span>) : "…"}</dd>
              <dt className="text-ink2">Projects</dt>
              <dd className="tabular-nums">{projects ? projects.length : "…"}</dd>
            </dl>
          )}
        </div>
      </section>

      <section className="grid gap-4">
        <div className="flex items-baseline justify-between border-b border-rule2 pb-2">
          <h2 className="font-display text-2xl font-semibold">Get started</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Step n={1} title="Set up the AI" done={aiDone} href="/settings" cta="AI connection">
            Use a free model running on this PC (Ollama), or add an Anthropic API key for Claude. Keys stay on this
            PC and are never sent to the browser.
          </Step>
          <Step n={2} title="Create a project" done={hasProject} href="/projects?new=1" cta="New project">
            Project code, name, client and floor, plus the National Annex choice. Engineering values stay in the
            design basis file.
          </Step>
          <Step n={3} title="Import drawings" done={hasFiles} href={hasProject ? `/projects/${projects![0].id}` : "/projects?new=1"} cta="Open a project">
            DXF and DWG are read and previewed (DWG via your AutoCAD 2023). PDF is viewable. DWF and DWFX are stored.
          </Step>
        </div>
      </section>

      {hasProject && (
        <section className="grid gap-3">
          <div className="flex items-baseline justify-between border-b border-rule2 pb-2">
            <h2 className="font-display text-2xl font-semibold">Recent projects</h2>
            <Link href="/projects" className="text-sm text-accent hover:underline">All projects</Link>
          </div>
          <ul className="grid gap-2">
            {projects!.slice(0, 4).map((p) => (
              <li key={p.id}>
                <Link href={`/projects/${p.id}`} className="panel flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3 hover:border-ink">
                  <span className="font-mono text-sm font-medium">{p.code}</span>
                  <span className="font-semibold">{p.name}</span>
                  <span className="text-sm text-ink2">{NA_LABEL[p.na_mode]}</span>
                  <span className="ml-auto text-sm tabular-nums text-ink2">{p.file_count ?? 0} file(s)</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="grid gap-3">
        <div className="flex items-baseline justify-between border-b border-rule2 pb-2">
          <h2 className="font-display text-2xl font-semibold">What works today</h2>
          <span className="label">Development Plan v2</span>
        </div>
        <ol className="grid border border-rule2 sm:grid-cols-5">
          {ROADMAP.map((m) => (
            <li key={m.id} className={`grid content-start gap-1 border-b border-rule p-3 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0 ${m.live ? "bg-accentsoft" : ""}`}>
              <span className="font-display text-xl font-bold text-accent">{m.id}</span>
              <span className="text-sm font-semibold">{m.name}</span>
              <span className="text-[13px] leading-snug text-ink2">{m.text}</span>
              <span className={`mt-1 font-mono text-[10.5px] uppercase ${m.live ? "text-ok" : "text-ink2"}`}>{m.live ? "available" : "not built yet"}</span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
