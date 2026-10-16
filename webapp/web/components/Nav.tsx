"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { aiReady, api, type AIStatus } from "@/lib/api";

export function AIPill({ status, error }: { status: AIStatus | null; error?: string | null }) {
  if (error) return <span className="rounded-sm bg-badsoft px-2 py-0.5 font-mono text-[11px] text-bad">Server offline</span>;
  if (!status) return <span className="font-mono text-[11px] text-ink2">…</span>;
  const label = status.models.find((m) => m.id === status.model)?.label ?? status.model;
  if (!aiReady(status)) {
    const why = status.provider === "ollama" ? (status.ollama.running ? "model not downloaded" : "Ollama not running") : "no API key";
    return <span className="rounded-sm bg-warnsoft px-2 py-0.5 font-mono text-[11px] text-warn">{label} · {why}</span>;
  }
  const tested = status.last_test?.ok && status.last_test.model === status.model;
  return (
    <span className={`rounded-sm px-2 py-0.5 font-mono text-[11px] ${tested ? "bg-oksoft text-ok" : "bg-accentsoft text-accent"}`}>
      {label} · {status.provider === "ollama" ? "ready, free" : tested ? "connected" : "key saved, not tested"}
    </span>
  );
}

export default function Nav() {
  const path = usePathname();
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.aiStatus().then(setStatus, (e: Error) => setError(e.message));
  }, [path]);

  const link = (href: string, label: string) => {
    const active = href === "/" ? path === "/" : path.startsWith(href);
    return (
      <Link href={href} className={`px-1 py-1 text-sm ${active ? "border-b-2 border-ink font-semibold" : "text-ink2 hover:text-ink"}`}>
        {label}
      </Link>
    );
  };

  return (
    <header className="border-b border-rule2 bg-sheet">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="font-display text-2xl font-bold tracking-wide">PT Designer</span>
          <span className="label hidden sm:inline">bonded band beam &amp; slab</span>
        </Link>
        <nav className="flex items-center gap-5">
          {link("/projects", "Projects")}
          {link("/settings", "AI connection")}
        </nav>
        <div className="ml-auto">
          <Link href="/settings"><AIPill status={status} error={error} /></Link>
        </div>
      </div>
    </header>
  );
}
