# AGENTS.md — AI Agent Operating Contract

This repository defines the intended state of this workstation.

When the computer has been rebuilt, reset, or appears incomplete:

1. Determine the user’s original task.
2. **Do not delete persistent storage.**
3. Inspect the current environment before changing it.
4. Preserve projects, databases, browser profiles, credentials, and service state.
5. Run the workstation doctor for the capabilities required by the user’s task.
6. Bootstrap only missing or incompatible capabilities.
7. Repair only diagnosed recoverable failures.
8. Run the doctor again.
9. Write a machine-readable report.
10. Continue the user’s original task.

**Do not turn workstation maintenance into an endless project.**
Install only what the current task or selected profile requires.

## Connector-first hierarchy

Prefer in this order:

1. Official connector or platform integration
2. Authenticated API or purpose-built CLI
3. Playwright / browser automation
4. Computer-use / GUI automation

Examples:
- GitHub connector or `gh` before browser clicking
- Gmail connector before browser clicking
- Drive connector before browser clicking
- Service API before screen scraping

## Mandatory safety rules

- Never delete `/workspace` during recovery.
- Never print credentials.
- Never commit secrets.
- Never overwrite an existing Git repository without inspection.
- Never reset Git history merely because a working tree is dirty.
- Never destroy Docker volumes during routine repair.
- Never run destructive `rclone sync` without explicit authorization.
- Never expose n8n publicly to make a health check pass.
- Never disable TLS verification as a routine fix.
- Never approve an arbitrary `.envrc`.
- Never run untrusted pull-request code with `sudo`.
- Never replace an existing real directory with a symlink without preserving and validating its contents.
- Never kill an unidentified process merely to free a port.
- Never claim that shared-agent directories provide security isolation.
- Never conceal a failed or skipped verification.

## Recovery levels

- **R1** — Persistent state survived → fully automated reinstall + repair
- **R2** — Persistent state lost but encrypted backup exists → restore + reauthorize
- **R3** — Everything lost → rebuild public software only; mark credentials as not_configured

## Quick agent commands

```bash
# Inspect current state (read-only)
./doctor.sh --profile core

# Install missing capabilities for core profile
./bootstrap.sh --profile core

# Targeted repair
./repair.sh --profile core

# Individual tool
./bootstrap.sh --tool playwright
./doctor.sh --tool playwright
```

After the doctor reports the required capabilities as ready, **continue the user’s original task**.
