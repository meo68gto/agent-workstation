# Grok Bot Recovery Guide

## After a computer rebuild (most common)

1. Confirm `/workspace` still exists and is writable.
2. Run:
   ```bash
   ./doctor.sh --profile core
   ```
3. If the doctor reports missing tools:
   ```bash
   ./bootstrap.sh --profile core
   ```
4. Re-run the doctor. Required capabilities should now be present.
5. Continue the original task.

**Do not** delete `/workspace` or regenerate n8n encryption keys / browser profiles.

## Multi-Bot notes

All Bots for the same member share the same computer and Unix user.  
Use an optional `AGENT_ID` environment variable if you want per-Bot log/report isolation:

```bash
export AGENT_ID=research-bot
./bootstrap.sh --profile core
```

Locks are process-based; two Bots starting bootstrap simultaneously are protected by flock, but they can still see each other’s files.

## What cannot be recovered automatically

- Lost n8n encryption key (existing credentials become unusable)
- Browser cookies / authenticated sessions that were never backed up
- Platform connectors that require re-authorization
- Any secret deliberately excluded from the sensitive backup set
