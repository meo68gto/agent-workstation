#!/usr/bin/env python3
"""Minimal orchestrator for Agent Workstation.

This is the hand-off target from stage-zero bootstrap.sh.
It currently implements detection, planning, and a read-only doctor
sufficient to prove the architecture. Full install/repair adapters
are the next implementation layer.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("PyYAML is required. Stage-zero should have installed it.", file=sys.stderr)
    sys.exit(5)


REPO_ROOT = Path(os.environ.get("AGENT_WORKSTATION_REPO", Path(__file__).resolve().parents[2]))
STATE_ROOT = Path(os.environ.get("AGENT_WORKSTATION_STATE", Path.home() / ".local/state/agent-workstation"))
RUN_ID = os.environ.get("AGENT_WORKSTATION_RUN_ID", datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
PROFILE = os.environ.get("AGENT_WORKSTATION_PROFILE", "core")
TOOL = os.environ.get("AGENT_WORKSTATION_TOOL", "")
DRY_RUN = os.environ.get("AGENT_WORKSTATION_DRY_RUN", "0") == "1"
JSON_MODE = os.environ.get("AGENT_WORKSTATION_JSON", "0") == "1"
VERBOSE = os.environ.get("AGENT_WORKSTATION_VERBOSE", "0") == "1"


def log(level: str, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] [{level}] {msg}", file=sys.stderr)


def load_tools() -> list[dict[str, Any]]:
    path = REPO_ROOT / "manifests" / "tools.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)
    tools = data.get("tools", [])
    if len(tools) != 50:
        log("ERROR", f"Expected exactly 50 tools, found {len(tools)}")
        sys.exit(2)
    return tools


def load_profiles() -> dict[str, Any]:
    path = REPO_ROOT / "manifests" / "profiles.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)
    return data.get("profiles", {})


def detect_host() -> dict[str, Any]:
    return {
        "hostname": platform.node(),
        "os": platform.system().lower(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "distro": _detect_distro(),
    }


def _detect_distro() -> str:
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "unknown"


def check_command(cmd: str) -> dict[str, Any]:
    path = shutil.which(cmd)
    if not path:
        return {"installed": False, "path": None, "version": None}
    version = None
    try:
        r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
        version = (r.stdout or r.stderr or "").splitlines()[0][:120] if r.returncode == 0 else None
    except Exception:
        pass
    return {"installed": True, "path": path, "version": version}


def doctor(tools: list[dict], profile_name: str) -> dict[str, Any]:
    profiles = load_profiles()
    profile = profiles.get(profile_name, {})
    required_ids = set(profile.get("required", []))
    if profile_name == "all":
        required_ids = {t["id"] for t in tools}

    results = []
    summary = {
        "passed": 0,
        "warnings": 0,
        "failed": 0,
        "not_configured": 0,
        "unsupported": 0,
        "skipped": 0,
        "blocked": 0,
    }

    for t in tools:
        tid = t["id"]
        primary = t.get("commands", {}).get("primary", [])
        alts = t.get("commands", {}).get("alternatives", [])
        cmds = primary + alts

        status = "skipped"
        installed = False
        version = None
        path = None
        reason = "Not selected by profile"

        if tid in required_ids or TOOL == tid:
            if not cmds:
                # library or service capability
                status = "not_configured"
                reason = "Service/library capability — detailed check not yet implemented"
                summary["not_configured"] += 1
            else:
                found = None
                for c in cmds:
                    info = check_command(c)
                    if info["installed"]:
                        found = info
                        break
                if found:
                    installed = True
                    path = found["path"]
                    version = found["version"]
                    status = "passed"
                    reason = "Command present"
                    summary["passed"] += 1
                else:
                    status = "failed"
                    reason = f"None of {cmds} found on PATH"
                    summary["failed"] += 1
        else:
            summary["skipped"] += 1

        results.append({
            "id": tid,
            "number": t["number"],
            "name": t["name"],
            "installed": installed,
            "status": status,
            "path": path,
            "version": version,
            "reason": reason,
        })

    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "operation": "doctor",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile_name,
        "host": detect_host(),
        "state": {
            "root": str(STATE_ROOT),
            "persistence_confidence": "unknown",
        },
        "summary": summary,
        "tools": results,
        "completion_label": "implemented-not-fully-verified",
    }


def main() -> int:
    log("INFO", f"Agent Workstation orchestrator v0.1.0-dev  run={RUN_ID}")
    log("INFO", f"Profile={PROFILE}  tool={TOOL or '(none)'}  dry_run={DRY_RUN}")

    tools = load_tools()
    log("INFO", f"Loaded {len(tools)} primary capabilities")

    report = doctor(tools, PROFILE)

    # Write report
    report_dir = STATE_ROOT / "reports" / "runs" / RUN_ID
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "doctor-report.json"
    with report_path.open("w") as f:
        json.dump(report, f, indent=2)
    log("INFO", f"Report written to {report_path}")

    if JSON_MODE:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        print()
        print("AI AGENT WORKSTATION DOCTOR")
        print(f"Run: {RUN_ID}")
        print(f"Profile: {PROFILE}")
        print(f"Host: {report['host'].get('distro')} ({report['host'].get('architecture')})")
        print(f"State root: {STATE_ROOT}")
        print()
        print(f"Passed:          {s['passed']}")
        print(f"Failed:          {s['failed']}")
        print(f"Not configured:  {s['not_configured']}")
        print(f"Skipped:         {s['skipped']}")
        print()
        if s["failed"] == 0:
            print("PROFILE READY (core checks passed — full verification still pending)")
        else:
            print("PROFILE NOT FULLY READY — missing required capabilities")
        print()
        print(f"Completion label: {report['completion_label']}")

    if report["summary"]["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
