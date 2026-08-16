#!/usr/bin/env python3
"""Agent Workstation orchestrator — doctor, bootstrap, and repair."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from .aliases import apply_aliases, plan_aliases
from .catalog import load_debian_map, load_tools_for_profile, resolve_profile
from .context import (
    dry_run,
    ensure_process_path,
    json_mode,
    log,
    operation,
    profile_name,
    run_id,
    state_root,
    tool_filter,
)
from .install import install_missing
from .verify import verify_tool
from . import context as ctx


def selected_ids(tools: list[dict[str, Any]], profile: dict[str, Any]) -> set[str]:
    wanted = set(profile["required"])
    if tool_filter():
        wanted.add(tool_filter())
    return wanted


def doctor_tools(tools: list[dict[str, Any]], wanted: set[str]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    summary = {
        "passed": 0,
        "warnings": 0,
        "failed": 0,
        "not_configured": 0,
        "unsupported": 0,
        "skipped": 0,
        "blocked": 0,
    }
    results: list[dict[str, Any]] = []
    for tool in tools:
        tid = tool["id"]
        if tid not in wanted:
            summary["skipped"] += 1
            results.append(
                {
                    "id": tid,
                    "number": tool["number"],
                    "name": tool["name"],
                    "installed": False,
                    "status": "skipped",
                    "path": None,
                    "version": None,
                    "reason": "Not selected by profile",
                    "checks": [],
                }
            )
            continue
        outcome = verify_tool(tool)
        if outcome.status in summary:
            summary[outcome.status] += 1
        else:
            summary["failed"] += 1
        results.append(
            {
                "id": tid,
                "number": tool["number"],
                "name": tool["name"],
                "installed": outcome.installed,
                "status": outcome.status,
                "path": outcome.path,
                "version": outcome.version,
                "reason": outcome.reason,
                "checks": outcome.checks,
            }
        )
    return results, summary


def build_report(
    op: str,
    profile: dict[str, Any],
    tool_results: list[dict[str, Any]],
    summary: dict[str, int],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    failed = summary.get("failed", 0)
    label = "verified" if failed == 0 and op != "doctor" else "implemented-not-fully-verified"
    if op == "doctor" and failed == 0:
        label = "verified"
    report = {
        "schema_version": 1,
        "run_id": run_id(),
        "operation": op,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile["name"],
        "host": ctx.detect_host(),
        "state": {
            "root": str(state_root()),
            "persistence_confidence": "high" if ctx.detect_host().get("debian_like") else "unknown",
        },
        "summary": summary,
        "tools": tool_results,
        "completion_label": label,
    }
    if extra:
        report.update(extra)
    return report


def write_report(report: dict[str, Any], name: str) -> None:
    report_dir = state_root() / "reports" / "runs" / run_id()
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / name
    with path.open("w") as fh:
        json.dump(report, fh, indent=2)
    log("INFO", f"Report written to {path}")


def print_human(report: dict[str, Any]) -> None:
    s = report["summary"]
    print()
    print(f"AI AGENT WORKSTATION {report['operation'].upper()}")
    print(f"Run: {report['run_id']}")
    print(f"Profile: {report['profile']}")
    print(f"Host: {report['host'].get('distro')} ({report['host'].get('architecture')})")
    print(f"State root: {report['state']['root']}")
    print()
    print(f"Passed:          {s.get('passed', 0)}")
    print(f"Failed:          {s.get('failed', 0)}")
    print(f"Not configured:  {s.get('not_configured', 0)}")
    print(f"Blocked:         {s.get('blocked', 0)}")
    print(f"Skipped:         {s.get('skipped', 0)}")
    if report.get("install"):
        print()
        print("Install actions:")
        for item in report["install"]:
            print(f"  {item.get('id')}: {item.get('status')} — {item.get('reason')}")
    if report.get("aliases"):
        print()
        print("Path aliases:")
        for item in report["aliases"]:
            print(f"  {item.get('to')}: {item.get('status')} — {item.get('reason')}")
    print()
    if s.get("failed", 0) == 0:
        print("PROFILE READY")
    else:
        print("PROFILE NOT FULLY READY — missing required capabilities")
        missing = [t["id"] for t in report["tools"] if t["status"] == "failed"]
        if missing:
            print("Failed: " + ", ".join(missing))
    print()
    print(f"Completion label: {report['completion_label']}")


def run_doctor(tools: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    ensure_process_path()
    results, summary = doctor_tools(tools, selected_ids(tools, profile))
    return build_report("doctor", profile, results, summary)


def ensure_profile(tools: list[dict[str, Any]], profile: dict[str, Any], op: str) -> dict[str, Any]:
    ensure_process_path()
    debian_map = load_debian_map()
    wanted = selected_ids(tools, profile)
    before_results, before_summary = doctor_tools(tools, wanted)
    missing = [t["id"] for t in before_results if t["status"] in {"failed", "not_configured"} and t["id"] in wanted]
    # Libraries/services with no adapter stay not_configured; still attempt if adapter exists.
    install_ids = []
    by_id = {t["id"]: t for t in tools}
    for tid in missing:
        strategy = (by_id[tid].get("install") or {}).get("preferred_strategy")
        if strategy:
            install_ids.append(tid)

    install_results = install_missing(tools, install_ids, debian_map, dry=dry_run())
    ensure_process_path()

    alias_tools = [by_id[tid] for tid in wanted if tid in by_id]
    alias_results = apply_aliases(plan_aliases(alias_tools, debian_map), dry=dry_run())
    ensure_process_path()

    after_results, after_summary = doctor_tools(tools, wanted)
    extra = {
        "install": install_results,
        "aliases": alias_results,
        "before": before_summary,
    }
    report = build_report(op, profile, after_results, after_summary, extra)
    return report


def main() -> int:
    op = operation()
    log("INFO", f"Agent Workstation orchestrator v0.1.0-dev  run={run_id()}  op={op}")
    log("INFO", f"Profile={profile_name()}  tool={tool_filter() or '(none)'}  dry_run={dry_run()}")

    try:
        profile = resolve_profile(profile_name())
        tools = load_tools_for_profile(profile)
    except Exception as exc:
        log("ERROR", str(exc))
        return 2

    if profile.get("catalog") == "agent-stack":
        venv_py = ctx.state_root() / "venvs" / "agent-stack" / "bin" / "python"
        if venv_py.exists():
            os.environ["AGENT_WORKSTATION_PYTHON"] = str(venv_py)

    log("INFO", f"Loaded {len(tools)} capabilities from {profile.get('catalog', 'primary')}; profile requires {len(profile['required'])}")

    if op == "doctor":
        report = run_doctor(tools, profile)
        write_report(report, "doctor-report.json")
    elif op in {"bootstrap", "repair"}:
        report = ensure_profile(tools, profile, op)
        write_report(report, f"{op}-report.json")
        write_report({k: report[k] for k in report if k != "install"}, "doctor-report.json")
    else:
        log("ERROR", f"Unknown operation: {op}")
        return 2

    if json_mode():
        print(json.dumps(report, indent=2))
    else:
        print_human(report)

    if report["summary"].get("failed", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    if __package__ in {None, ""}:
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from workstation.cli import main as packaged_main

        raise SystemExit(packaged_main())
    raise SystemExit(main())
