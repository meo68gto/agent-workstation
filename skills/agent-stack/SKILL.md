---
name: agent-stack
description: >
  Productionize the Grok Bot agent stack (browser-use, Mem0, LangGraph,
  Langfuse, Firecrawl, CrewAI, Pydantic AI, Mastra). Use when asked to
  add agent frameworks, long-term memory, observability, Firecrawl,
  crews, or to run the productionize-agent-stack outline.
---

# Agent stack

## Read first

1. [prompts/productionize-agent-stack.md](../../prompts/productionize-agent-stack.md) — user outline (do not replace).
2. [docs/AGENT-STACK.md](../../docs/AGENT-STACK.md) — audit, coexistence, phases.
3. [manifests/agent-stack.yaml](../../manifests/agent-stack.yaml) — licenses, MCP, install, verify.

## Rules

- This stack is a **second catalog**. Do not add these eight frameworks/services to `manifests/tools.yaml`.
- Prefer self-host / local-first. Bind services to `127.0.0.1`.
- Do not enable Langfuse or Mastra `ee/` features.
- Do not vendor Firecrawl source into this MIT repo (AGPL-3.0).
- Do not start Docker compose unless `docker info` works and the user has not forbidden it.
- Do not print API keys. Do not commit `.env`.
- Do not replace workstation state with Mem0.
- Follow the web hierarchy in AGENTS.md (Firecrawl before browser-use before computer-use).
- Stop for secrets, public exposure of n8n/Langfuse/Firecrawl, or `rclone sync`.

## Execute

```bash
./doctor.sh --profile agent-stack
./bootstrap.sh --profile agent-stack
python3 scripts/validate-agent-stack.py
```

Work the next `phases[].status` that is not `in_repo` / `done`.  
Default next: **python-libs**, plus a local JSON trace fallback. Langfuse compose waits on Docker.

## Done when

- Doctor for `agent-stack` reports python-lib verify results honestly.
- Validation script writes a machine-readable summary.
- Any missing Docker service is `blocked` or `not_configured`, never silently passed.
