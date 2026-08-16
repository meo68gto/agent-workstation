# Agent stack on Grok Bot

Grok Bot is non-root, member-scoped, and may not have Docker or passwordless sudo.

## Do

- Keep stack state under `/workspace/.agent-workstation` (venv, traces, Mem0 local store).
- Install Python libraries into `<state-root>/venvs/agent-stack` (no sudo).
- Bind Langfuse/Firecrawl to loopback if Docker ever works.
- Share Mem0 scopes across Bots on this computer; they already share the Unix user.

## Do not

- Assume `sudo` or `docker`.
- Add the Bot user to the docker group (`defaults.yaml`).
- Wipe browser profiles to make browser-use pass.
- Run Firecrawl or Langfuse on a public interface.
- Treat hosted Browser Use Cloud / Mem0 Cloud / Firecrawl Cloud as the default. Local-first first.

## Reality check (2026-08-16)

The `core` install path is on PR #2, not `main`. A Bot that only `git pull origin main` still cannot self-heal CLI tools. The agent-stack outline can still be read and planned; library install still needs `uv` from `core`.
