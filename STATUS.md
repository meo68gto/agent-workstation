# Build Status — Agent Workstation

**Date**: 2026-08-14
**Completion label**: `implemented-not-fully-verified`

## What is complete and live on GitHub

- Repository created and public: https://github.com/meo68gto/agent-workstation
- MIT License
- Full README with recovery guarantees and profile overview
- Complete AGENTS.md operating contract (safety rules, recovery levels, connector-first hierarchy)
- Stage-zero `bootstrap.sh` (host detection, state-root resolution, locking, Python ensure, hand-off)
- `manifests/profiles.yaml` (all profiles: minimal, core, developer, browser, data, automation, media, backup, security, all)
- Python package skeleton (`src/workstation/`)
- Directory structure matching the architecture contract

## Local (ready to push / next commits)

- Full `manifests/tools.yaml` with **exactly 50** primary capabilities, correct numbers, categories, canonical projects, license classifications (n8n correctly marked `source_available`), primary commands, and basic verification contracts.
- Minimal but functional orchestrator (`src/workstation/cli.py`) that loads the catalog, runs a profile-aware doctor, writes machine-readable reports, and respects the status model.

## Still required for full `verified`

1. Capability adapters for all 50 tools (install/configure/verify/repair)
2. Full source lock (`locks/sources.lock.yaml`) with digests
3. Schema validation + CI workflows
4. Backup / restore implementation (standard + sensitive sets)
5. n8n Docker Compose service with loopback binding and encryption-key handling
6. Idempotency + failure-injection test suites
7. Clean Debian 13 smoke + privileged VM evidence
8. Remaining documentation (ARCHITECTURE, RECOVERY, TOOL-CATALOG, THREAT-MODEL, ADRs)

## How to continue

```bash
git clone https://github.com/meo68gto/agent-workstation.git
cd agent-workstation
./bootstrap.sh --help
# After next push of tools.yaml + cli.py:
./bootstrap.sh --profile core
./doctor.sh --profile core --json
```

The architecture contracts from the Master Build Prompt are preserved. The foundation is solid and the next implementation layers can be added incrementally without breaking the stage-zero or doctor path.
