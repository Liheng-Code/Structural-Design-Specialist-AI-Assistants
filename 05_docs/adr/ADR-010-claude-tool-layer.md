# ADR-010 - Claude through a server-side tool layer

Status: ACCEPTED (user, 16-OCT-2026). Applies from M6; Claude Code + skills remain the interface until then.

## Decision
- Claude is called only from the API server, using the Anthropic Python SDK. API keys never reach the browser or the logs.
- Claude acts only through tools. Each tool has a Pydantic input schema (ADR-005), validates its input, and returns structured results or an explicit error.
- Only implemented and tested tools are exposed (v1 Part 15).
- Tools that touch check results are read-only. No tool can change a check status, record an approval or issue a package.
- Numbers in Claude's replies must come from tool results.
- Text from uploaded CAD files and other external files is treated as untrusted data, never as instructions.
- Every tool call is logged with user, project, inputs and outcome.
- The model is chosen per task in configuration, not hard-coded.

## Consequences
- Claude can't produce or alter an engineering result; it can only run approved tools and explain their output.

## Amendment 1 - local models (ACCEPTED, user, 16-OCT-2026)
The user asked for a free option with no usage limit. The assistant may also run on open models served locally by Ollama on the engineer's PC (default: Qwen3 14B; Phi-4 14B as an alternative). Claude stays available as the paid option (Haiku 5.5 first, per the user's low-cost preference).
- Every rule above applies to local models too: server-side only, tools only, read-only on check results, no approval or issue tools, numbers only from tool results, uploaded text treated as data.
- Local models are weaker at reasoning and tool use than Claude. When tools arrive (M2+), each tool workflow is tested on the model that will run it; a workflow that a local model can't do reliably is restricted to Claude rather than run unreliably.
- Local models keep project data on the PC (nothing sent to a third party). Hosted free tiers that train on submitted data (e.g. Gemini free tier, Mistral Experiment tier) are not used for project data.
- Open-model licences are checked before any commercial distribution of the app.
