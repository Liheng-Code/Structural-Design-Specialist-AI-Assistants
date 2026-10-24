# AI access - Claude, local Ollama models, other assistants, GitHub, NotebookLM

Everything runs on the local PC. The project is reachable in four ways:

| Route | For | What it gives |
|---|---|---|
| `AGENTS.md` + `CLAUDE.md` + `.claude/skills/` | Claude Code, Copilot, Codex, Gemini CLI, Cursor, Continue, Cline (any agent opened on this folder) | Rules, discipline map, skills |
| MCP server `04_tools/ai/mcp_server.py` | Any MCP client: Claude Code, Claude Desktop, Open WebUI (via mcpo), Continue, Cline, LM Studio | Read-only tools: list disciplines, discipline briefing, read / list / search files, list and validate design bases |
| `04_tools/ai/ask_local.py` | Local Ollama model from the terminal (default `qwen3:14b`) | Questions answered from the retrieved project text |
| `06_knowledge-pack/` | NotebookLM (and any chat tool that accepts uploaded files) | One Markdown source per discipline + shared core |

The MCP server is read-only: no tool writes files, approves, issues or changes a result (ADR-010). It never serves `.git/`, `webapp/data/` (API key, uploads) or `.env` files.

## Install once
```
py -3 -m pip install mcp pyyaml
```

## Claude Code
`.mcp.json` in the repo root registers the server as `structural-project`. Open the folder in Claude Code and approve the server when asked (or run `/mcp`).

## Claude Desktop
Settings -> Developer -> Edit config, add (use your own path):
```json
{
  "mcpServers": {
    "structural-project": {
      "command": "py",
      "args": ["-3", "D:\\Structural Design Specialist AI Assistants\\tools\\ai\\mcp_server.py"]
    }
  }
}
```

## Local Ollama model
Terminal (no extra packages):
```
ollama serve                      # if not already running
python 04_tools/ai/ask_local.py --discipline pt-floor "Which inputs are missing before PT screening?"
python 04_tools/ai/ask_local.py --discipline rc-works            # interactive
python 04_tools/ai/ask_local.py --discipline steel --show-sources "base plate"   # see what would be sent
```
Options: `--model` (or env `OLLAMA_MODEL`), `--host` (or env `OLLAMA_HOST_URL`), `--num-ctx` (default 16384).

With tools (the model calls the MCP server itself) - pick one client:
- **VS Code - Continue or Cline:** set the model provider to Ollama `qwen3:14b`; add an MCP server with command `py` and args `-3 <repo>\tools\ai\mcp_server.py`.
- **Open WebUI:** expose the server as an OpenAPI tool with mcpo: `uvx mcpo --port 8000 -- py -3 04_tools/ai/mcp_server.py`, then add `http://localhost:8000` under Settings -> Tools.

Tool calling works best with models that support it (Qwen3 does). Small local models make more mistakes: treat answers as drafts.

## Other cloud AIs (ChatGPT, Gemini, Copilot)
- Coding agents opened on the repo (Copilot, Codex, Gemini CLI, Cursor) read `AGENTS.md`.
- Chat apps: upload the `06_knowledge-pack/` files, or connect the GitHub repo where the app supports it (the repo is private: grant access per app).

## GitHub
Remote: `origin` -> `https://github.com/Liheng-Code/Structural-Design-Specialist-AI-Assistants` (private). Normal flow:
```
git add -A
git commit -m "..."
git push origin <branch>
```
Before pushing: run the tests, and if knowledge, skills or standards changed, rebuild the knowledge pack and commit it with the change (`06_knowledge-pack/` is tracked in git). `webapp/data/` is git-ignored and must stay out of the repo.

## NotebookLM
1. `python 04_tools/knowledge/build_knowledge_pack.py`
2. In NotebookLM: new notebook -> Add source -> Upload -> the `.md` files in `06_knowledge-pack/`. Details: `06_knowledge-pack/README.md`.
3. To let Claude Code query it: share the notebook (Share -> anyone with the link, or your account) and give Claude the link; it registers it with the NotebookLM MCP (`add_notebook`) and can then ask questions.
4. Re-upload after each rebuild. NotebookLM is a recall aid, not a source to cite (gap G29).
