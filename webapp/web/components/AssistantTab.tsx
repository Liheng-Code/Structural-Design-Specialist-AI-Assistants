"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { aiReady, api, type AIStatus, type ChatMessage } from "@/lib/api";

const SUGGESTIONS = [
  "Which of the uploaded files can you see, and what can the app read from each?",
  "What information is still missing before a PT design can start for this project?",
  "Explain what the National Annex choice changes for this project.",
];

export default function AssistantTab({ projectId }: { projectId: string }) {
  const [ai, setAi] = useState<AIStatus | null>(null);
  const [msgs, setMsgs] = useState<ChatMessage[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.aiStatus().then(setAi, () => undefined);
    api.chat(projectId).then(setMsgs, (e: Error) => setErr(e.message));
  }, [projectId]);
  useEffect(() => {
    // Braces matter: newer browsers return a Promise from scrollIntoView, and an effect may only return a cleanup.
    end.current?.scrollIntoView({ block: "end" });
  }, [msgs, busy]);

  async function send(t: string) {
    const q = t.trim();
    if (!q || busy) return;
    setBusy(true);
    setErr(null);
    setText("");
    const temp: ChatMessage = { id: -Date.now(), role: "user", display: q, model: null, created_at: new Date().toISOString() };
    setMsgs((m) => [...m, temp]);
    try {
      await api.send(projectId, q);
      setMsgs(await api.chat(projectId));
    } catch (e) {
      setMsgs((m) => m.filter((x) => x.id !== temp.id));
      setText(q);
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function clear() {
    await api.clearChat(projectId);
    setMsgs([]);
  }

  const noKey = !!ai && !aiReady(ai);
  const modelLabel = ai?.models.find((m) => m.id === ai.model)?.label ?? ai?.model;
  const local = ai?.provider === "ollama";

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-sm text-ink2">
          The assistant sees this project&apos;s details and file list. It can&apos;t open the files or run calculations yet,
          and it&apos;s told not to state code values or results you haven&apos;t given it.
        </p>
        <span className="ml-auto font-mono text-xs text-ink2">{modelLabel}</span>
        {msgs.length > 0 && <button className="btn-ghost px-2.5 py-1 text-xs" onClick={clear} disabled={busy}>Clear conversation</button>}
      </div>

      {noKey && (
        <p className="rounded-sm bg-warnsoft px-3 py-2 text-sm text-warn">
          {local
            ? (ai!.ollama.running ? `${modelLabel} isn't downloaded yet. ` : "Ollama isn't running on this PC. ")
            : "Claude isn't connected yet. "}
          <Link href="/settings" className="font-semibold underline">Open AI connection</Link> to fix it.
        </p>
      )}
      {local && !noKey && msgs.length === 0 && (
        <p className="text-xs text-ink2">Runs on this PC: free and private. The first reply can take up to a minute while the model loads.</p>
      )}

      <div className="panel grid max-h-[560px] min-h-[320px] content-start gap-4 overflow-y-auto p-4">
        {msgs.length === 0 && !busy && (
          <div className="grid gap-2">
            <p className="label">Try asking</p>
            {SUGGESTIONS.map((s) => (
              <button key={s} disabled={noKey} onClick={() => send(s)} className="border border-rule px-3 py-2 text-left text-sm hover:border-ink disabled:opacity-50">{s}</button>
            ))}
          </div>
        )}
        {msgs.map((m) => (
          <div key={m.id} className={`grid max-w-[80ch] gap-1 ${m.role === "user" ? "justify-self-end" : ""}`}>
            <span className="label">{m.role === "user" ? "You" : `Assistant${m.model ? ` · ${ai?.models.find((x) => x.id === m.model)?.label ?? m.model}` : ""}`}</span>
            <div className={`whitespace-pre-wrap px-3 py-2 text-[14.5px] ${m.role === "user" ? "bg-accentsoft" : "border-l-2 border-accent bg-paper"}`}>{m.display}</div>
          </div>
        ))}
        {busy && <p className="text-sm text-ink2">{modelLabel} is writing…</p>}
        <div ref={end} />
      </div>

      {err && <p role="alert" className="rounded-sm bg-badsoft px-3 py-2 text-sm text-bad">{err}</p>}

      <form onSubmit={(e) => { e.preventDefault(); send(text); }} className="flex gap-2">
        <textarea
          id="chat-input"
          rows={2}
          className="field flex-1 resize-y"
          placeholder={noKey ? "Set up the AI connection first" : "Ask about this project…  (Enter to send, Shift+Enter for a new line)"}
          value={text}
          disabled={noKey || busy}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(text); } }}
        />
        <button className="btn-primary self-end" disabled={noKey || busy || !text.trim()}>Send</button>
      </form>
    </div>
  );
}
