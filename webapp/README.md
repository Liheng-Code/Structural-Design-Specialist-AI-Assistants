# PT Designer web app (local mockup)

An early slice of milestone M6 (Development Plan v2), brought forward so the workspace can be seen and used while the engineering core is built. It uses the accepted stack: Next.js + TypeScript + Tailwind (ADR-009) and FastAPI (ADR-005). Storage is local, under `webapp/data/`; Supabase replaces it at M6 (ADR-008).

## Run

Double-click `start_webapp.bat`, or run these in two terminals:

```
cd webapp/api && py -m uvicorn main:app --host 127.0.0.1 --port 8000
cd webapp/web && npm run dev
```

Then open http://localhost:3000.

First-time setup: `py -m pip install -r webapp/api/requirements.txt` and `cd webapp/web && npm install`. For the free local model: install Ollama from ollama.com, then run `ollama pull qwen3:14b` (about 9 GB).

## What works

| Feature | State |
|---|---|
| Landing page with setup steps and PC status | Working |
| AI connection: model choice and connection test | Working. **Default: Qwen3 14B running locally through Ollama** (free, no usage limit, nothing leaves the PC; ADR-010 amendment 1). Claude (Haiku 5.5 first) is the paid option; its key is stored in `webapp/data/settings.json` on this PC and never returned to the browser. |
| Create and list projects | Working. Identification and the National Annex choice only; engineering values stay in the design basis YAML (ADR-003). |
| Import DXF | Read with ezdxf (version, units, layers, entity counts) plus a black-on-white SVG preview |
| Import DWG | Converted to DXF with AutoCAD 2023 `accoreconsole` on this PC, then read like a DXF. Without AutoCAD the file is stored and you're asked for a DXF. |
| Import PDF | Page count and size; viewed in the browser |
| Import DWF / DWFX | Stored and identified only. They're viewing formats, so no geometry is extracted. |
| Import XLSX / XLS / CSV | Stored; SAFE/ETABS import arrives at M1 |
| Project assistant | Local model or Claude. Sees the project details and file list; no calculation tools yet. Opus, Sonnet and Fable requests use Anthropic's server-side refusal fallback. |
| Geometry, analysis, PT design, drawings tabs | Shown disabled with the milestone that delivers them |

## Limits (mockup)

- No sign-in or roles yet: anyone who can open localhost:3000 on this PC can use it. The servers listen on 127.0.0.1 only.
- One AutoCAD conversion runs at a time, with a 120 s limit.
- Nothing produced here is an engineering result or an approval.
