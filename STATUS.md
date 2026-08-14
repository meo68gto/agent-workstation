# Build Status — Agent Workstation

**Date**: 2026-08-14
**Completion label**: `implemented-not-fully-verified`

## What is complete and live on GitHub

- Repository: https://github.com/meo68gto/agent-workstation
- MIT License, full README, AGENTS.md, CHANGELOG
- Stage-zero `bootstrap.sh`
- `manifests/profiles.yaml` (all profiles)
- Working doctor orchestrator (`src/workstation/cli.py`)
- **Grok Bot platform adapter** (`platforms/grok-cloud/`):
  - README with research-backed facts
  - `defaults.yaml` (hard `/workspace` preference, non-root, never wipe auth profiles / n8n keys, multi-Bot notes)
  - `detect.sh`
  - `recovery.md`
- MCP examples tuned for `/workspace`
- Skills directory stub

## Grok Bot specific improvements applied

1. Platform adapter for Grok cloud computers
2. Strong preference for `/workspace/.agent-workstation` as durable state root
3. Explicit multi-Bot / shared-UID warnings and optional `AGENT_ID` support
4. Security defaults: never add to Docker group, never regenerate n8n encryption key if state exists, never wipe authenticated browser profiles, bind services to loopback
5. MCP example servers that target `/workspace`
6. Recovery guide written for the common “computer rebuilt, /workspace survived” case

## Still required for full `verified`

1. Full `manifests/tools.yaml` push + all 50 capability adapters
2. Source lock with digests
3. Schema + CI
4. Backup/restore (standard + sensitive)
5. n8n Compose service with encryption-key handling
6. Idempotency + failure-injection tests
7. Debian 13 evidence
8. Remaining documentation

## How to use on Grok Bot

```bash
# After clone
./doctor.sh --profile core
./bootstrap.sh --profile core   # only if tools are missing
# Optional per-Bot isolation
export AGENT_ID=my-bot
```

See `platforms/grok-cloud/recovery.md` for the rebuild recovery sequence.
