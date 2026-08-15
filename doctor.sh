#!/usr/bin/env bash
# doctor.sh — read-only workstation health check
# Thin wrapper around the Python orchestrator in doctor mode.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AGENT_WORKSTATION_REPO="$REPO_ROOT"

# Force doctor operation
export AGENT_WORKSTATION_OPERATION="doctor"

# Re-use the stage-zero entrypoint logic by calling bootstrap with doctor intent.
# The Python orchestrator currently implements the doctor path.
exec "$REPO_ROOT/bootstrap.sh" "$@"
