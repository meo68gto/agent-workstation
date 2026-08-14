#!/usr/bin/env bash
# Stage-zero bootstrap entrypoint for Agent Workstation
# Responsibilities (strictly limited):
# 1. Safe shell behavior
# 2. Detect host
# 3. Determine target non-root user
# 4. Determine state root
# 5. Create private log/lock directories
# 6. Acquire bootstrap lock
# 7. Install/locate minimal parser/orchestrator prerequisites
# 8. Launch the real orchestrator
# 9. Return orchestrator exit code
#
# Do not require jq, yq, just, or other catalog capabilities here.

set -euo pipefail
IFS=$'\n\t'

# ---------- constants ----------
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"
readonly RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
readonly LOG_DIR_DEFAULT="${XDG_STATE_HOME:-$HOME/.local/state}/agent-workstation/logs/runs"

# ---------- helpers ----------
log() {
  local level="$1"; shift
  printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$*" >&2
}

die() {
  log "ERROR" "$*"
  exit 3  # blocked / prerequisite failure
}

# ---------- argument parsing (minimal) ----------
PROFILE="core"
STATE_ROOT=""
DRY_RUN=0
NON_INTERACTIVE=0
VERBOSE=0
NO_SUDO=0
JSON=0
TOOL=""
REPAIR=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="${2:-}"; shift 2 ;;
    --tool) TOOL="${2:-}"; shift 2 ;;
    --state-root) STATE_ROOT="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --verbose) VERBOSE=1; shift ;;
    --no-sudo) NO_SUDO=1; shift ;;
    --json) JSON=1; shift ;;
    --repair) REPAIR=1; shift ;;
    --help|-h)
      cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Stage-zero bootstrap for Agent Workstation.

Options:
  --profile NAME       Profile to bootstrap (default: core)
  --tool ID            Bootstrap a single capability
  --state-root PATH    Explicit state root
  --dry-run            Plan only, no mutation
  --non-interactive    Never prompt
  --verbose            Extra logging
  --no-sudo            Refuse privileged operations
  --json               Machine-readable output on stdout
  --repair             Attempt targeted repairs after install
  --help               Show this help

Exit codes:
  0  Required capabilities passed
  1  One or more required capabilities failed
  2  Invalid arguments / manifest
  3  Blocked (unsupported host, missing privilege, etc.)
  4  Lock contention
  5  Internal orchestration failure
EOF
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

# ---------- safety ----------
umask 077

# ---------- detect target user ----------
if [[ $EUID -eq 0 ]]; then
  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    TARGET_USER="$SUDO_USER"
  else
    log "WARN" "Running as root with no identifiable non-root target user"
    TARGET_USER="root"
  fi
else
  TARGET_USER="$(id -un)"
fi

# ---------- resolve state root ----------
resolve_state_root() {
  if [[ -n "$STATE_ROOT" ]]; then
    echo "$STATE_ROOT"
    return
  fi
  if [[ -n "${AGENT_WORKSTATION_STATE:-}" ]]; then
    echo "$AGENT_WORKSTATION_STATE"
    return
  fi
  if [[ -d /workspace && -w /workspace ]]; then
    echo "/workspace/.agent-workstation"
    return
  fi
  if [[ -n "${XDG_STATE_HOME:-}" ]]; then
    echo "${XDG_STATE_HOME}/agent-workstation"
    return
  fi
  echo "${HOME}/.local/state/agent-workstation"
}

STATE_ROOT="$(resolve_state_root)"
mkdir -p "$STATE_ROOT"/{logs/runs,locks,reports/runs,journals}
chmod 700 "$STATE_ROOT"

LOG_DIR="$STATE_ROOT/logs/runs"
LOCK_FILE="$STATE_ROOT/locks/bootstrap.lock"
RUN_LOG="$LOG_DIR/${RUN_ID}.log"

exec > >(tee -a "$RUN_LOG") 2>&1

log "INFO" "Agent Workstation stage-zero bootstrap"
log "INFO" "Run ID: $RUN_ID"
log "INFO" "Repo: $REPO_ROOT"
log "INFO" "Target user: $TARGET_USER"
log "INFO" "State root: $STATE_ROOT"
log "INFO" "Profile: $PROFILE"
[[ -n "$TOOL" ]] && log "INFO" "Tool: $TOOL"

# ---------- acquire lock ----------
if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    log "ERROR" "Bootstrap lock held by another process"
    exit 4
  fi
  # write diagnostic metadata
  cat >"$LOCK_FILE.meta" <<EOF
pid=$$
user=$TARGET_USER
run_id=$RUN_ID
started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
operation=bootstrap
profile=$PROFILE
EOF
else
  log "WARN" "flock not available; proceeding without exclusive lock"
fi

# ---------- ensure Python 3 (stage-zero exception) ----------
ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    local ver
    ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    log "INFO" "Python 3 found: $ver"
    return 0
  fi

  if [[ $NO_SUDO -eq 1 ]]; then
    die "Python 3 required but not present and --no-sudo was specified"
  fi

  if command -v apt-get >/dev/null 2>&1; then
    log "INFO" "Installing python3 via apt (stage-zero)"
    if [[ $EUID -eq 0 ]]; then
      DEBIAN_FRONTEND=noninteractive apt-get update -qq
      DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-yaml python3-jsonschema
    else
      sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-yaml python3-jsonschema
    fi
  else
    die "Python 3 not found and no supported package manager available"
  fi
}

ensure_python

# ---------- launch orchestrator ----------
export AGENT_WORKSTATION_RUN_ID="$RUN_ID"
export AGENT_WORKSTATION_STATE="$STATE_ROOT"
export AGENT_WORKSTATION_REPO="$REPO_ROOT"
export AGENT_WORKSTATION_PROFILE="$PROFILE"
export AGENT_WORKSTATION_TOOL="$TOOL"
export AGENT_WORKSTATION_DRY_RUN="$DRY_RUN"
export AGENT_WORKSTATION_NON_INTERACTIVE="$NON_INTERACTIVE"
export AGENT_WORKSTATION_VERBOSE="$VERBOSE"
export AGENT_WORKSTATION_NO_SUDO="$NO_SUDO"
export AGENT_WORKSTATION_JSON="$JSON"
export AGENT_WORKSTATION_REPAIR="$REPAIR"
export AGENT_WORKSTATION_TARGET_USER="$TARGET_USER"

ORCHESTRATOR="$REPO_ROOT/src/workstation/cli.py"

if [[ ! -f "$ORCHESTRATOR" ]]; then
  log "WARN" "Python orchestrator not yet fully implemented — running stage-zero only"
  log "INFO" "State root and logs are ready at $STATE_ROOT"
  log "INFO" "Next: implement src/workstation/cli.py and capability adapters"
  exit 0
fi

log "INFO" "Handing off to Python orchestrator"
exec python3 "$ORCHESTRATOR" "$@"
