#!/usr/bin/env bash
# repair.sh — targeted repair of diagnosed recoverable failures
# Reuses stage-zero bootstrap, then runs the orchestrator in repair mode.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AGENT_WORKSTATION_REPO="$REPO_ROOT"
export AGENT_WORKSTATION_OPERATION="repair"

exec "$REPO_ROOT/bootstrap.sh" "$@"
