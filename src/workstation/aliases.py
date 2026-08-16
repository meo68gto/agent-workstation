"""Create primary-name shims for Debian-renamed binaries."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .catalog import path_aliases_for
from .context import log, user_bin


def plan_aliases(
    tools: list[dict[str, Any]],
    debian_map: dict[str, Any],
    dest_dir: Path | None = None,
) -> list[dict[str, Any]]:
    dest_dir = dest_dir or user_bin()
    planned: list[dict[str, Any]] = []
    for tool in tools:
        for alias in path_aliases_for(tool, debian_map):
            source_name = alias.get("from")
            target_name = alias.get("to")
            if not source_name or not target_name:
                continue
            planned.append(
                {
                    "id": tool["id"],
                    "from": source_name,
                    "to": target_name,
                    "source": _resolve_source(source_name),
                    "dest": str(dest_dir / target_name),
                }
            )
    return planned


def _resolve_source(name: str) -> str | None:
    import shutil

    return shutil.which(name)


def apply_aliases(plan: list[dict[str, Any]], dry: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in plan:
        dest = Path(item["dest"])
        source = item["source"]
        result = dict(item)
        if not source:
            result["status"] = "skipped"
            result["reason"] = f"{item['from']} not on PATH"
            results.append(result)
            continue
        source_path = Path(source).resolve()
        if dest.exists() or dest.is_symlink():
            try:
                if dest.resolve() == source_path:
                    result["status"] = "present"
                    result["reason"] = "alias already correct"
                    results.append(result)
                    continue
            except Exception:
                pass
            if dest.is_dir() and not dest.is_symlink():
                result["status"] = "blocked"
                result["reason"] = f"refusing to replace directory {dest}"
                results.append(result)
                continue
            if dest.exists() and not dest.is_symlink():
                result["status"] = "blocked"
                result["reason"] = f"refusing to replace existing file {dest}"
                results.append(result)
                continue
        if dry:
            result["status"] = "planned"
            result["reason"] = f"would link {dest} -> {source_path}"
            results.append(result)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink():
            dest.unlink()
        os.symlink(source_path, dest)
        if hasattr(os, "chmod"):
            dest.chmod(0o755)
        log("INFO", f"Alias {dest} -> {source_path}")
        result["status"] = "created"
        result["reason"] = f"linked {dest.name} -> {source_path}"
        results.append(result)
    return results
