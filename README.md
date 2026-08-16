# Agent Workstation

**Self-healing, vendor-neutral AI Agent Workstation** for Linux (Debian 13 / Trixie primary target).

Bootstrap, diagnose, repair, and recover an AI agent’s Linux environment after a fresh deployment, partial reset, or cloud-computer rebuild while strictly preserving user data and credentials.

## Quick Start

```bash
git clone https://github.com/meo68gto/agent-workstation.git
cd agent-workstation
./bootstrap.sh --profile core
./doctor.sh --profile core
```

For the full catalog (50 primary capabilities):

```bash
./bootstrap.sh --profile all
./doctor.sh --profile all
```

## What this recovers

- Missing CLI tools, runtimes, and services
- Broken or missing configurations (managed blocks only)
- Playwright browser binaries
- Docker client/daemon readiness (when supported)
- n8n service (loopback-bound, state-preserving)
- Standard and sensitive backup sets

## What this does **not** automatically recover

- Lost third-party account credentials
- Lost private keys or n8n encryption keys
- Lost browser cookies / authentication sessions
- Cloud data that was never backed up
- Platform-managed connectors that require reauthorization

## Recovery Guarantees

| Level | Condition | Expected result |
|-------|-----------|-----------------|
| **R1** | Persistent state survived | Automated reinstall + targeted repair |
| **R2** | Usable encrypted backup exists | Isolated restore + reauthorization |
| **R3** | State + secrets lost | Public software only; credentials marked `not_configured` |

## Profiles

- `minimal` — inspect, diagnose, safe bootstrap
- `core` — recommended baseline for AI cloud workstations
- `developer` — toolchains + repo quality
- `browser` — Playwright + yt-dlp
- `data` — JupyterLab, DuckDB, pandas, Miller
- `automation` — Docker + n8n
- `media` — FFmpeg, ImageMagick, Tesseract, Poppler, Pandoc
- `backup` — rsync, rclone, restic
- `security` — age + SOPS
- `all` — full 50-capability catalog

## Architecture highlights

- **Stage-zero** pure Bash entrypoint → Python orchestrator
- Canonical `manifests/tools.yaml` (exactly 50 primary capabilities)
- Debian package map (`manifests/debian.yaml`) plus PATH aliases (`fdfind`→`fd`, `batcat`→`bat`)
- Pinned source lock (`locks/sources.lock.yaml`) for official releases
- Install adapters: `apt`, `official_release`, `official_apt_repository`
- Doctor runs catalog `verify:` contracts (exec / python / http)
- Idempotent, non-destructive, resumable
- XDG-aware persistent state; `/workspace` preferred on Grok Bot
- Unit tests + Debian 13 core-profile smoke in CI

## AI Agent instruction

```
Read AGENTS.md and restore this workstation. Preserve all existing user data.
Run the doctor, install only what is missing, repair recoverable failures,
verify the required capabilities, and then continue my original task.
```

## Documentation

- [AGENTS.md](AGENTS.md) — operating contract for agents
- [platforms/grok-cloud/README.md](platforms/grok-cloud/README.md) — Grok Bot adapter
- [platforms/grok-cloud/recovery.md](platforms/grok-cloud/recovery.md) — rebuild recovery
- [STATUS.md](STATUS.md) — current completion label

## License

MIT (see [LICENSE](LICENSE)).  
Third-party tools retain their own licenses.  
n8n is classified as **source-available** (Sustainable Use License / fair-code), not OSI open-source.

---

**Status**: Active development toward v0.1.0  
**Primary target**: Debian 13 (Trixie) amd64  
**Current scope**: `core` profile install + doctor is implemented. Backup/restore, n8n service, and remaining strategy adapters (`uv-tool`, `pnpm`, `docker-compose`) are not.
