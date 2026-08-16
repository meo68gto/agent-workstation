#!/usr/bin/env python3
"""Validation suite for the hardcoded agent-stack outline (prompt items a–f).

Does not invent success. Missing Docker/libs are blocked or failed.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("AGENT_WORKSTATION_REPO", str(ROOT))

from workstation.catalog import load_stack_tools  # noqa: E402
from workstation.context import state_root  # noqa: E402
from workstation.verify import verify_tool  # noqa: E402


CHECKS = {
    "a": "firecrawl",
    "b": "browser-use",
    "c": "mem0",
    "d": "langgraph",
    "e": "pydantic-ai",
    "f": "langfuse",
}


def main() -> int:
    venv_py = state_root() / "venvs" / "agent-stack" / "bin" / "python"
    if venv_py.exists():
        os.environ["AGENT_WORKSTATION_PYTHON"] = str(venv_py)

    by_id = {t["id"]: t for t in load_stack_tools(ROOT)}
    results = []
    for letter, tool_id in CHECKS.items():
        outcome = verify_tool(by_id[tool_id])
        results.append(
            {
                "id": letter,
                "tool": tool_id,
                "status": outcome.status,
                "reason": outcome.reason,
            }
        )

    traces = list((state_root() / "traces").glob("*.json")) if (state_root() / "traces").exists() else []
    if not any(r["tool"] == "langfuse" and r["status"] == "passed" for r in results):
        results.append(
            {
                "id": "f-fallback",
                "tool": "local-json-spans",
                "status": "passed" if traces else "not_configured",
                "reason": f"{len(traces)} local trace file(s)" if traces else "no Langfuse and no local traces",
            }
        )

    report = {
        "schema_version": 1,
        "suite": "agent-stack",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "passed": sum(1 for r in results if r["status"] == "passed"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "blocked_or_missing": sum(1 for r in results if r["status"] in {"not_configured", "blocked"}),
    }
    print(json.dumps(report, indent=2))
    if report["failed"] > 0:
        return 1
    # Suite is allowed to exit 0 when only environment-dependent items are missing.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
