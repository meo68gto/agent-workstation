#!/usr/bin/env bash
# Debian smoke: bootstrap --profile core must finish with failed: 0.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${AGENT_WORKSTATION_SMOKE_IMAGE:-debian:trixie-slim}"

exec docker run --rm \
  -e DEBIAN_FRONTEND=noninteractive \
  -v "$ROOT:/src:ro" \
  "$IMAGE" \
  bash -lc '
    set -euo pipefail
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
      ca-certificates curl python3 python3-yaml xz-utils tar sudo \
      >/dev/null
    mkdir -p /work /workspace
    cp -a /src /work/agent-workstation
    cd /work/agent-workstation
    chmod +x bootstrap.sh doctor.sh repair.sh
    export AGENT_WORKSTATION_STATE=/workspace/.agent-workstation
    set +e
    ./bootstrap.sh --profile core --non-interactive --json >/tmp/bootstrap.json
    boot_rc=$?
    set -e
    echo "bootstrap_exit=$boot_rc"
    python3 - <<'"'"'PY'"'"'
import json, pathlib, sys
state = pathlib.Path("/workspace/.agent-workstation/reports/runs")
reports = sorted(state.glob("*/doctor-report.json"))
if not reports:
    print("no doctor-report.json written", file=sys.stderr)
    sys.exit(1)
report = json.loads(reports[-1].read_text())
failed = report.get("summary", {}).get("failed", 99)
print(json.dumps({"report": str(reports[-1]), "summary": report.get("summary"), "failed_tools": [t["id"] for t in report.get("tools", []) if t.get("status")=="failed"]}, indent=2))
sys.exit(0 if failed == 0 else 1)
PY
  '
