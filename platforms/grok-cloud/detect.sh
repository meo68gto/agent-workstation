#!/usr/bin/env bash
# Best-effort detection of a Grok Bot / Grok cloud environment.
# Exit 0 if likely Grok cloud, non-zero otherwise.
# This script is read-only and safe to run at any time.

set -euo pipefail

score=0

# Strong signal: writable /workspace
if [[ -d /workspace && -w /workspace ]]; then
  score=$((score + 3))
fi

# Non-root is expected
if [[ $EUID -ne 0 ]]; then
  score=$((score + 1))
fi

# Common managed-VM indicators (conservative)
if [[ -n "${HOSTNAME:-}" ]]; then
  case "$HOSTNAME" in
    *grok*|*xai*|*cloud*|*bot*) score=$((score + 1)) ;;
  esac
fi

# No traditional graphical session is common
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  score=$((score + 1))
fi

if [[ $score -ge 4 ]]; then
  echo "grok-cloud"
  exit 0
fi

exit 1
