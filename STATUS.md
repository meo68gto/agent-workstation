# Build Status — Agent Workstation

**Date**: 2026-08-15
**Latest**: install adapters + verify contracts + source lock + repair.sh
**Completion label**: `verified` for `core` profile install+doctor on Debian 13 (Docker `debian:trixie-slim`, 17/17, `failed: 0`)

## Now in the tree

- `bootstrap.sh --profile core` installs missing required tools, then doctors
- `repair.sh` reuses the same ensure path
- Doctor executes catalog `verify:` contracts (not just `which`)
- Debian aliases: `fdfind` → `fd`, `batcat` → `bat`
- `locks/sources.lock.yaml` pins uv, node, pnpm, yq, just, and the GitHub CLI apt repo
- `manifests/debian.yaml` maps apt package names
- Unit tests + `tests/smoke/core-bootstrap.sh`

## What to do on the cloud computer

```bash
git pull origin main
chmod +x doctor.sh bootstrap.sh repair.sh
./bootstrap.sh --profile core
```

## Agent stack (2026-08-16)

The productionize prompt is hardcoded. It is **not** installed on a Grok Bot yet.

- Outline: `prompts/productionize-agent-stack.md`
- Catalog: `manifests/agent-stack.yaml` (8 tools, separate from the 50)
- Profile: `./doctor.sh --profile agent-stack`
- Python-lib adapter: `uv-pip` into `<state-root>/venvs/agent-stack`
- Langfuse/Firecrawl remain Docker-gated; Firecrawl is AGPL and must stay out of this tree

## Remaining

- Adapters for `uv-tool`, `pnpm` (Playwright), and `docker-compose` (n8n)
- Isolated backup/restore
- Broader profile smoke (`developer`, `all`)
- Idempotency + failure-injection CI
