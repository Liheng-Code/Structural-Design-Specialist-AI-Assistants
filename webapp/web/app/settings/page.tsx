"use client";

import { useEffect, useState } from "react";
import { aiReady, api, type AIModel, type AIStatus } from "@/lib/api";

export default function Settings() {
  const [s, setS] = useState<AIStatus | null>(null);
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState<"save" | "test" | "clear" | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const refresh = () => api.aiStatus().then(setS, (e: Error) => setMsg({ ok: false, text: e.message }));
  useEffect(() => { refresh(); }, []);

  async function run(kind: "save" | "test" | "clear", fn: () => Promise<void>) {
    setBusy(kind);
    setMsg(null);
    try {
      await fn();
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    } finally {
      setBusy(null);
    }
  }

  const test = () => run("test", async () => {
    const r = await api.testAI();
    await refresh();
    setMsg({
      ok: true,
      text: s?.provider === "ollama"
        ? `Ready. ${r.display_name} is downloaded and Ollama is running. Free to use, no limit.`
        : `Connected. ${r.display_name} (${r.model}) is available to this key. This test is free and doesn't check credits.`,
    });
  });
  const pickModel = (model: string) => run("save", async () => {
    setS(await api.saveAI({ model }));
    setMsg({ ok: true, text: "Model saved. Test it to confirm it's ready." });
  });
  const saveKey = () => run("save", async () => {
    setS(await api.saveAI({ api_key: key }));
    setKey("");
    setMsg({ ok: true, text: "Key saved. Select a Claude model and test it." });
  });
  const clearKey = () => run("clear", async () => {
    setS(await api.saveAI({ clear_key: true }));
    setMsg({ ok: true, text: "Key removed from this PC." });
  });

  const group = (provider: AIModel["provider"]) => s?.models.filter((m) => m.provider === provider) ?? [];
  const downloaded = (m: AIModel) => {
    const name = m.id.replace(/^ollama:/, "");
    return !!s?.ollama.models.some((x) => x === name || x === `${name}:latest`);
  };

  const ModelOption = ({ m }: { m: AIModel }) => (
    <label className={`flex cursor-pointer items-start gap-3 border px-3 py-2.5 ${s?.model === m.id ? "border-ink bg-accentsoft" : "border-rule hover:border-rule2"}`}>
      <input id={`model-${m.id}`} type="radio" name="model" className="mt-1" checked={s?.model === m.id} onChange={() => pickModel(m.id)} />
      <span className="grid flex-1">
        <span className="flex flex-wrap items-baseline gap-x-2 font-medium">
          {m.label}
          {m.provider === "ollama" && (
            <span className={`font-mono text-[10.5px] ${downloaded(m) ? "text-ok" : "text-warn"}`}>{downloaded(m) ? "downloaded" : "not downloaded"}</span>
          )}
        </span>
        <span className="text-sm text-ink2">{m.note}</span>
      </span>
    </label>
  );

  return (
    <div className="grid max-w-3xl gap-8">
      <header className="grid gap-2 border-b-2 border-ink pb-4">
        <p className="label">Settings</p>
        <h1 className="font-display text-4xl font-bold">AI connection</h1>
        <p className="text-ink2">
          Choose which model answers in the project assistant. Local models run on this PC for free with no usage limit,
          and nothing leaves the PC. Claude models are stronger but paid per use through your Anthropic account.
        </p>
      </header>

      <section className="panel grid gap-4 p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-display text-2xl font-semibold">Model</h2>
          {s && <span className={`font-mono text-xs ${aiReady(s) ? "text-ok" : "text-warn"}`}>{aiReady(s) ? "selected model is ready" : "selected model isn't ready"}</span>}
        </div>
        <fieldset className="grid gap-4" disabled={busy !== null}>
          <legend className="sr-only">Model</legend>
          <div className="grid gap-2">
            <p className="label">Free · on this PC (Ollama)</p>
            {group("ollama").map((m) => <ModelOption key={m.id} m={m} />)}
          </div>
          <div className="grid gap-2">
            <p className="label">Claude · paid, needs an API key with credits</p>
            {group("anthropic").map((m) => <ModelOption key={m.id} m={m} />)}
          </div>
        </fieldset>
        <div className="flex flex-wrap items-center gap-3">
          <button className="btn-primary" onClick={test} disabled={!s || busy !== null}>{busy === "test" ? "Testing…" : "Test selected model"}</button>
        </div>
        {msg && <p role="status" className={`rounded-sm px-3 py-2 text-sm ${msg.ok ? "bg-oksoft text-ok" : "bg-badsoft text-bad"}`}>{msg.text}</p>}
      </section>

      <section className="panel grid gap-3 p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-display text-2xl font-semibold">Local models (Ollama)</h2>
          {s && (
            <span className={`font-mono text-xs ${s.ollama.running ? "text-ok" : "text-warn"}`}>
              {s.ollama.running ? `running · version ${s.ollama.version}` : "not running"}
            </span>
          )}
        </div>
        {s && !s.ollama.running && (
          <p className="text-sm text-ink2">Start the <b>Ollama</b> app from the Start menu (it runs in the system tray), then reload this page. Not installed? Get it from ollama.com.</p>
        )}
        {s?.ollama.running && (
          <>
            <p className="text-sm text-ink2">Downloaded: {s.ollama.models.length ? <span className="font-mono">{s.ollama.models.join(", ")}</span> : "none yet"}</p>
            <p className="text-xs text-ink2">To add a model, open a terminal and run <code className="font-mono">ollama pull qwen3:14b</code> or <code className="font-mono">ollama pull phi4</code> (about 9 GB each), then reload.</p>
          </>
        )}
      </section>

      <section className="panel grid gap-4 p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-display text-2xl font-semibold">Claude API key</h2>
          {s && (
            <span className="font-mono text-xs text-ink2">
              {s.key_source === "none" ? "no key set" : `key ${s.key_hint} (from ${s.key_source === "settings" ? "this app" : "ANTHROPIC_API_KEY"})`}
            </span>
          )}
        </div>
        <p className="text-sm text-ink2">Only needed for Claude models. Stored by the app server on this PC (webapp/data/settings.json), never sent back to the browser.</p>
        <label className="grid gap-1.5">
          <span className="text-sm font-medium">Anthropic API key</span>
          <input id="api-key" type="password" autoComplete="off" className="field font-mono"
            placeholder={s?.key_source !== "none" ? "Leave empty to keep the current key" : "sk-ant-…"}
            value={key} onChange={(e) => setKey(e.target.value)} />
          <span className="text-xs text-ink2">From console.anthropic.com → API keys. Chat use is billed to that account and needs credits.</span>
        </label>
        <div className="flex flex-wrap gap-3">
          <button className="btn-ghost" onClick={saveKey} disabled={!key || busy !== null}>{busy === "save" ? "Saving…" : "Save key"}</button>
          {s?.key_source === "settings" && <button className="btn-ghost text-bad" onClick={clearKey} disabled={busy !== null}>Remove key</button>}
        </div>
        <p className="text-xs text-ink2">Opus, Sonnet and Fable requests use Anthropic&apos;s automatic fallback: if the model declines for safety reasons, the API retries on another model.</p>
      </section>
    </div>
  );
}
