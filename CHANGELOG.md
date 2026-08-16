# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0-dev] - 2026-08-16

### Added
- Hardcoded Grok Bot productionize outline (`prompts/productionize-agent-stack.md`)
- Second catalog `manifests/agent-stack.yaml` (8 frameworks/services)
- `agent-stack` profile, skill, docs, MCP examples, validation script
- `uv-pip` adapter for isolated agent-stack venv
- AGENTS.md hierarchy: Firecrawl → browser-use → Playwright → computer-use

## [0.1.0-dev] - 2026-08-15

### Added
- Install adapters for `apt`, `official_release`, and `official_apt_repository`
- `repair.sh` entrypoint (AGENTS.md contract)
- Catalog `verify:` execution (exec, python, http)
- Debian PATH aliases for `fd` and `bat`
- `locks/sources.lock.yaml` with sha256-pinned core official releases
- `manifests/debian.yaml` package map
- Profile `extends` resolution
- Unit tests and Debian 13 core-profile smoke test

### Changed
- `bootstrap.sh --profile core` now installs missing required tools, then runs doctor
- README no longer links to documentation files that are not in the tree

## [0.1.0-dev] - 2026-08-14

### Added
- Public repository created under meo68gto/agent-workstation
- MIT License
- Full README with recovery guarantees and profile overview
- Complete AGENTS.md operating contract (safety rules, connector-first hierarchy, recovery levels)
- Stage-zero bootstrap.sh (host detection, state-root resolution, locking, Python ensure)
- manifests/profiles.yaml with all profiles (minimal, core, developer, browser, data, automation, media, backup, security, all)
- Working doctor orchestrator (src/workstation/cli.py) that loads the 50-capability catalog, evaluates profiles, and writes machine-readable reports
- STATUS.md tracking completion label

### Known gaps for full verification
- Full tools.yaml (50 capabilities) is prepared and validated locally; pending final push of large file
- Capability install/repair adapters not yet implemented
- Source lock, schemas, CI, backup/restore, n8n service still pending

### Completion label
implemented-not-fully-verified
