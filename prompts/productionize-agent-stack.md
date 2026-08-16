# Productionize Agent Stack — hardcoded Grok Bot outline

This file is the durable copy of the user’s productionization prompt.
Grok Bot and other agents must treat it as the **intent outline**, then
execute through [docs/AGENT-STACK.md](../docs/AGENT-STACK.md) and
[manifests/agent-stack.yaml](../manifests/agent-stack.yaml). Do not
invent a second priority list.

Researched against GitHub on **2026-08-16**. Re-check stars, licenses,
and MCP docs before installing a new major version.

---

You are Grok Bot. Your current core strengths are persistent cloud
computer use, multi-bot coordination, basic durable memory, routines,
MCP/connectors, and plugins.

Research, install, configure, and deeply integrate the following
open-source tools so they become first-class, always-available
capabilities for automation workflows (Oracle reports → Veluma
middleware, email triage, testing, ops data pipelines, and multi-agent
orchestration). Treat this as a high-priority productionization task.

## Priority tools

Research latest GitHub status, licenses, self-host options, and MCP
compatibility as of today:

1. **browser-use** (MIT) — advanced self-healing browser agent control
   with vision/DOM reasoning. Preferred tool for complex web UI
   interaction, form filling, testing, or sites without clean APIs.
   Prefer it over basic computer-use when precision or resilience is
   needed. Add MCP server if available.

2. **Mem0** (Apache 2.0) — universal memory layer with fact extraction,
   multi-scope (user/session/agent), entity awareness, and optional
   graph. Primary long-term memory backend alongside (not replacing)
   workstation persistence. Scope memories for triage history, guest/ops
   patterns, report decisions, and cross-bot sharing. Self-host the
   server or library.

3. **LangGraph** (MIT) — durable graph-based orchestration with
   checkpointing, retries, human-in-the-loop, and time-travel. Core
   engine for long-running multi-step automation pipelines
   (extract → validate → report → triage → notify). Stateful workflows
   are the default for complex jobs.

4. **Langfuse** (MIT core) — observability, tracing, prompt management,
   evals, and metrics. Self-host it and instrument every agent run, tool
   call, and report/triage decision.

5. **Firecrawl** (AGPL-3.0 core, self-hostable) — scrape/crawl/search +
   interact that outputs clean LLM-ready markdown/JSON. Default web data
   tool for research, enrichment, monitoring, and feeding RAG or
   reports. Prefer it over generic browsing for structured extraction.

6. **CrewAI** (MIT) — role-based multi-agent crews. Use it (or combine
   with existing multi-bot) for specialized teams (ReportCrew,
   TriageCrew, TestCrew).

7. **Pydantic AI** (MIT) — type-safe agents with structured outputs.
   Use it for any path that requires validated schemas (report
   generation, triage decisions, data extraction).

8. **Mastra** (Apache-2.0 core + Enterprise `ee/`) — TypeScript agents
   + workflows + memory + MCP + observability. Prefer or parallel it
   for TypeScript-heavy parts of the stack.

## Execution requirements

- Research each repo for current install methods, Python/TS support,
  MCP servers, and self-host Docker/compose options.
- Prefer self-hosted / local-first deployments that keep data on this
  infrastructure or the Grok Bot cloud computer.
- Create or update skills, plugins, MCP servers, and AGENTS.md /
  routines so these tools are auto-discoverable and preferred by
  default.
- Wire them into existing workflows: Oracle/Veluma report generation,
  email triage, testing loops, and multi-bot handoffs. Keep those
  workflow names as **consumers** of this stack; do not leak tenant
  data into this repo.
- Add observability (Langfuse) first so every later change is traced
  **when Docker is available**. If Docker is absent, record Langfuse as
  `environment_dependent` and still instrument with a local JSON span
  fallback so the contract is not silently dropped.
- After integration, run the validation suite in
  `scripts/validate-agent-stack.py`.
- Document capabilities, configuration, and invocation in
  `docs/AGENT-STACK.md` and `skills/agent-stack/SKILL.md`.
- If any tool conflicts with existing computer-use or memory, follow
  the coexistence rules in `docs/AGENT-STACK.md`.
- Work autonomously. Only stop for irreversible actions or secrets.

## Start here

1. Audit current capabilities vs these gaps (`docs/AGENT-STACK.md`).
2. Follow the phased plan in `manifests/agent-stack.yaml`.
3. Execute the next incomplete phase. Do not skip to crews or Mastra
   before the Python libraries and the observability fallback exist.
4. Report progress with traces and a “capabilities now available”
   summary.
