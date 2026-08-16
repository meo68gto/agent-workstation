"""Run catalog verify: contracts."""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


class VerifyResult:
    def __init__(
        self,
        status: str,
        reason: str,
        installed: bool = False,
        path: str | None = None,
        version: str | None = None,
        checks: list[dict[str, Any]] | None = None,
    ) -> None:
        self.status = status
        self.reason = reason
        self.installed = installed
        self.path = path
        self.version = version
        self.checks = checks or []

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "installed": self.installed,
            "path": self.path,
            "version": self.version,
            "checks": self.checks,
        }


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()[:160]
    return ""


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run_exec(argv: list[str], timeout: int = 15) -> dict[str, Any]:
    if not argv:
        return {"ok": False, "reason": "empty argv", "output": "", "path": None}
    path = _which(argv[0])
    if not path:
        return {"ok": False, "reason": f"{argv[0]} not on PATH", "output": "", "path": None}
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        return {"ok": False, "reason": f"{argv[0]} exec error: {exc}", "output": "", "path": path}
    output = _first_line(r.stdout) or _first_line(r.stderr)
    if r.returncode != 0:
        return {
            "ok": False,
            "reason": f"{' '.join(argv)} exited {r.returncode}",
            "output": output,
            "path": path,
        }
    return {"ok": True, "reason": "ok", "output": output, "path": path}


def run_python(code: str, timeout: int = 15) -> dict[str, Any]:
    return run_exec([sys.executable, "-c", code], timeout=timeout)


def run_http(url: str, timeout: int = 5) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=timeout) as resp:  # noqa: S310 — catalog-controlled health URLs
            status = getattr(resp, "status", 0)
            if 200 <= int(status) < 300:
                return {"ok": True, "reason": f"HTTP {status}", "output": str(status), "path": url}
            return {"ok": False, "reason": f"HTTP {status}", "output": str(status), "path": url}
    except URLError as exc:
        return {"ok": False, "reason": f"HTTP unreachable: {exc.reason}", "output": "", "path": url}
    except Exception as exc:
        return {"ok": False, "reason": f"HTTP error: {exc}", "output": "", "path": url}


def verify_tool(tool: dict[str, Any]) -> VerifyResult:
    checks: list[dict[str, Any]] = []
    steps = list(tool.get("verify") or [])
    primary = list((tool.get("commands") or {}).get("primary") or [])
    alts = list((tool.get("commands") or {}).get("alternatives") or [])

    if not steps:
        for cmd in primary + alts:
            info = run_exec([cmd, "--version"])
            checks.append({"id": "presence", "type": "exec", "ok": info["ok"], "detail": info["reason"]})
            if info["ok"]:
                return VerifyResult("passed", "Command present", True, info["path"], info["output"], checks)
        if not (primary or alts):
            return VerifyResult("not_configured", "No verify contract or commands", False, None, None, checks)
        return VerifyResult("failed", f"None of {primary + alts} found on PATH", False, None, None, checks)

    version = None
    path = None
    failed: list[str] = []
    http_only_failures = True
    saw_http = False
    saw_other = False

    for step in steps:
        step_id = step.get("id", "check")
        step_type = step.get("type")
        if step_type == "exec":
            saw_other = True
            info = run_exec(list(step.get("argv") or []))
            http_only_failures = False
        elif step_type == "python":
            saw_other = True
            info = run_python(str(step.get("code") or ""))
            http_only_failures = False
        elif step_type == "http":
            saw_http = True
            info = run_http(str(step.get("url") or ""))
        else:
            saw_other = True
            http_only_failures = False
            info = {"ok": False, "reason": f"unknown verify type {step_type}", "output": "", "path": None}

        checks.append({"id": step_id, "type": step_type, "ok": info["ok"], "detail": info["reason"]})
        if info["ok"]:
            version = version or info.get("output")
            path = path or info.get("path")
        else:
            failed.append(f"{step_id}: {info['reason']}")
            if step_type != "http":
                http_only_failures = False

    if not failed:
        return VerifyResult("passed", "Verify contracts passed", True, path, version, checks)

    # Service health URLs that are down are not_configured, not a missing package.
    if saw_http and not saw_other:
        return VerifyResult(
            "not_configured",
            "; ".join(failed),
            False,
            path,
            version,
            checks,
        )
    if http_only_failures and saw_http:
        return VerifyResult("not_configured", "; ".join(failed), False, path, version, checks)
    return VerifyResult("failed", "; ".join(failed), False, path, version, checks)
