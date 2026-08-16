# Agent Stack — audit, plan, coexistence

Hardcoded outline: [prompts/productionize-agent-stack.md](../prompts/productionize-agent-stack.md)  
Machine catalog: [manifests/agent-stack.yaml](../manifests/agent-stack.yaml)  
Bot skill: [skills/agent-stack/SKILL.md](../skills/agent-stack/SKILL.md)

Audited **2026-08-16**. This stack is **not** part of the primary CLI/service catalog.

## Current vs gap

| Need | Workstation today | Gap |
|---|---|---|
| CLI/runtime baseline | `core` profile (17 tools). Install path is on PR #2, not `main`. | Bot on `main` still cannot self-heal. |
| Observability | Run JSON reports only | No Langfuse. No span fallback yet. |
| Long-term memory | XDG/state + optional `AGENT_ID` (unused) | No Mem0. No fact extraction. |
| Durable pipelines | None | No LangGraph checkpoints. |
| Typed outputs | None | No Pydantic AI schemas. |
| Structured web extract | Playwright catalog row only; no adapter | No Firecrawl. |
| Interactive web | Computer-use (platform) + Playwright row | No browser-use. |
| Role crews | Multi-bot is a platform fact, not a framework | No CrewAI. |
| TypeScript agent framework | Node/pnpm in `core` | No Mastra workspace. |

Grok Bot constraints that override the prompt’s “install everything now”:

- Non-root. 13 of 17 `core` tools need sudo. Node is marked `requires_sudo`.
- Docker is environment-dependent (`defaults.yaml` forbids adding the user to the docker group).
- Langfuse and Firecrawl **require Docker**. They stay `environment_dependent` until a Bot run proves `docker info`.
- Firecrawl is **AGPL-3.0**. Self-host beside this repo. Do not copy its source into this MIT tree.
- Mastra and Langfuse have `ee/` enterprise folders. Do not enable them.

## Coexistence

**Memory.** Workstation state (`/workspace/.agent-workstation`) holds locks, doctor reports, and journals. Mem0 holds long-lived facts (triage history, ops patterns, report decisions). A fact never lives only in a chat transcript. Operational “did bootstrap run” never goes to Mem0.

**Web.** Connector/API first (already in AGENTS.md). Then Firecrawl for markdown/JSON extract. Then browser-use for multi-step UI. Then Playwright. Then computer-use. Do not open a browser to scrape a public docs page.

**Orchestration.** LangGraph is the default durable engine (checkpoint + retry + HITL). CrewAI is only for named crews. Mastra does not become a second Python orchestrator.

**Observability.** If Langfuse is up on loopback, every stack run sends a trace. If not, write `<state-root>/traces/<run-id>.json` and say so. Never claim “full Langfuse trace” without an id or a file.

## Phased plan

1. **contract** (this change) — outline, manifest, skill, AGENTS hierarchy, doctor profile.
2. **python-libs** — isolated venv: pydantic-ai, langgraph, mem0, browser-use, crewai.
3. **observability** — JSON spans immediately; Langfuse compose when Docker exists.
4. **firecrawl** — compose after AGPL ack; loopback only.
5. **mastra** — after `core` Node/pnpm works on the Bot.
6. **validate** — `scripts/validate-agent-stack.py`.

Do not skip to crews or Mastra before phase 2.

## How a Grok Bot should invoke this

```bash
# After checking out a revision that contains this stack:
./doctor.sh --profile agent-stack
./bootstrap.sh --profile agent-stack   # python libs only until Docker adapters exist
python3 scripts/validate-agent-stack.py
```

Read `skills/agent-stack/SKILL.md` before installing Docker services.

## Validation suite (prompt items a–f)

| Id | Check | Honest result until implemented |
|---|---|---|
| a | Firecrawl scrape | `blocked` without Docker + AGPL ack |
| b | browser-use multi-step | `failed` until venv + browser binaries |
| c | Mem0 multi-scope | `failed` until venv |
| d | LangGraph durable graph | `failed` until venv |
| e | Pydantic AI typed report | `failed` until venv |
| f | Langfuse full trace | `blocked` without Docker; else JSON fallback |

## Workflow consumers (names only)

Keep Oracle/Veluma, email triage, testing loops, and multi-bot handoffs as **callers**. This repo does not store tenant data, mailbox contents, or report payloads.
