# Grok Cloud / Grok Bot Platform Adapter

This adapter tunes Agent Workstation for **Grok Bot** (xAI’s managed Linux cloud computers).

## Key facts about Grok Bot (public research, Aug 2026)

- Each member receives **one dedicated managed Linux VM**.
- Multiple Bots belonging to the same member **share that single computer**.
- Files, browser sessions, sign-ins, and permissions are **member-scoped**, not Bot-scoped.
- Bots run as a **non-root** user.
- The computer can be rebuilt / reset; durable state must live in a location that survives rebuilds (commonly `/workspace`).
- Bots support MCP servers, plugins, browsing, and (with consent) local machine actions.

## What this adapter does

1. Detects a likely Grok Bot / Grok cloud environment.
2. Strongly prefers `/workspace/.agent-workstation` as the state root.
3. Emits clear persistence warnings when falling back to XDG paths.
4. Treats authenticated browser profiles and n8n encryption material as **critical + sensitive** and never regenerates or wipes them during normal bootstrap/repair.
5. Supports optional `AGENT_ID` for multi-Bot coordination on the same computer.
6. Marks capabilities that require root or Docker group membership as environment-dependent.

## Detection signals (best-effort)

- Presence of writable `/workspace`
- Non-root current user
- Hostname or environment patterns typical of managed cloud VMs
- Absence of a traditional desktop session

Exact internal signals may evolve; the adapter remains conservative and never assumes root.

## Recovery expectations

| Level | Typical Grok Bot situation | Workstation behavior |
|-------|---------------------------|----------------------|
| R1    | Computer rebuilt, `/workspace` survived | Fully automatic reinstall + reconnect |
| R2    | State lost but encrypted backup exists | Isolated restore + re-authorization |
| R3    | Everything lost | Rebuild public software only; mark credentials `not_configured` |

## Usage

The stage-zero bootstrap and doctor automatically prefer this adapter when `/workspace` is detected.  
You can also force it with environment variables or future `--platform grok-cloud` support.
