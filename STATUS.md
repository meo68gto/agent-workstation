# Build Status — Agent Workstation

**Date**: 2026-08-15
**Latest**: doctor.sh + tools.yaml structure pushed
**Completion label**: `implemented-not-fully-verified`

## Now on GitHub

- `doctor.sh`
- `manifests/tools.yaml` (structure + key entries including n8n as source_available)
- Full Grok Bot platform adapter
- Stage-zero bootstrap + doctor orchestrator

## What to do on the cloud computer right now

```bash
git pull origin main
chmod +x doctor.sh bootstrap.sh
./doctor.sh --profile core
```

The doctor path should now run. Install adapters are still missing, so bootstrap will not yet install missing packages — it will report them.

## Remaining for full usability

- Complete the middle entries of tools.yaml (currently abbreviated in the pushed version)
- Real install/repair adapters
- Source lock, CI, backup/restore, n8n service
