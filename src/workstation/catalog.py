"""Load tools, profiles, Debian maps, and the source lock."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from .context import log, repo_root


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data


def load_tools(root: Path | None = None) -> list[dict[str, Any]]:
    path = (root or repo_root()) / "manifests" / "tools.yaml"
    tools = _load_yaml(path).get("tools", [])
    if not tools:
        raise ValueError("tools.yaml contains no tools")
    ids = [t.get("id") for t in tools]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate tool ids in tools.yaml")
    numbers = [t.get("number") for t in tools]
    if numbers != list(range(1, len(tools) + 1)):
        raise ValueError("Tool numbers must be unique and sequential starting at 1")
    return tools


def tools_by_id(tools: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    return {t["id"]: t for t in (tools if tools is not None else load_tools())}


def load_profiles(root: Path | None = None) -> dict[str, Any]:
    path = (root or repo_root()) / "manifests" / "profiles.yaml"
    return _load_yaml(path).get("profiles", {})


def resolve_profile(
    name: str,
    profiles: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    profiles = profiles if profiles is not None else load_profiles()
    if name == "all":
        catalog = tools if tools is not None else load_tools()
        return {
            "name": "all",
            "description": profiles.get("all", {}).get("description", ""),
            "catalog": "primary",
            "required": [t["id"] for t in catalog],
            "recommended": list(profiles.get("all", {}).get("recommended", [])),
            "environment_dependent": list(profiles.get("all", {}).get("environment_dependent", [])),
        }
    if name not in profiles:
        raise KeyError(f"Unknown profile: {name}")

    required: list[str] = []
    recommended: list[str] = []
    env_dep: list[str] = []
    seen: set[str] = set()

    def walk(profile_name: str) -> None:
        if profile_name in seen:
            raise ValueError(f"Profile cycle involving {profile_name}")
        seen.add(profile_name)
        profile = profiles.get(profile_name)
        if profile is None:
            raise KeyError(f"Unknown profile: {profile_name}")
        parent = profile.get("extends")
        if parent:
            walk(parent)
        for item in profile.get("required", []):
            if item not in required:
                required.append(item)
        for item in profile.get("recommended", []):
            if item not in recommended:
                recommended.append(item)
        for item in profile.get("environment_dependent", []):
            if item not in env_dep:
                env_dep.append(item)

    walk(name)
    return {
        "name": name,
        "description": profiles[name].get("description", ""),
        "catalog": profiles[name].get("catalog", "primary"),
        "required": required,
        "recommended": recommended,
        "environment_dependent": env_dep,
    }


def load_stack_tools(root: Path | None = None) -> list[dict[str, Any]]:
    path = (root or repo_root()) / "manifests" / "agent-stack.yaml"
    data = _load_yaml(path)
    tools = data.get("tools", [])
    ids = [t.get("id") for t in tools]
    if len(ids) != 8:
        raise ValueError(f"Expected 8 agent-stack tools, found {len(ids)}")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate ids in agent-stack.yaml")
    return tools


def load_tools_for_profile(profile: dict[str, Any], root: Path | None = None) -> list[dict[str, Any]]:
    if profile.get("catalog") == "agent-stack":
        return load_stack_tools(root)
    return load_tools(root)


def load_debian_map(root: Path | None = None) -> dict[str, Any]:
    path = (root or repo_root()) / "manifests" / "debian.yaml"
    if not path.exists():
        return {"apt_packages": {}, "path_aliases": {}}
    return _load_yaml(path)


def load_source_lock(root: Path | None = None) -> dict[str, Any]:
    path = (root or repo_root()) / "locks" / "sources.lock.yaml"
    if not path.exists():
        log("WARN", f"Source lock missing: {path}")
        return {"tools": {}, "apt_repositories": {}}
    return _load_yaml(path)


def apt_packages_for(tool: dict[str, Any], debian_map: dict[str, Any] | None = None) -> list[str]:
    install = tool.get("install") or {}
    if install.get("apt_packages"):
        return list(install["apt_packages"])
    debian_map = debian_map if debian_map is not None else load_debian_map()
    mapped = (debian_map.get("apt_packages") or {}).get(tool["id"])
    if mapped:
        return list(mapped)
    return [tool["id"]]


def path_aliases_for(tool: dict[str, Any], debian_map: dict[str, Any] | None = None) -> list[dict[str, str]]:
    install = tool.get("install") or {}
    if install.get("path_aliases"):
        return list(install["path_aliases"])
    debian_map = debian_map if debian_map is not None else load_debian_map()
    mapped = (debian_map.get("path_aliases") or {}).get(tool["id"]) or []
    return list(mapped)


def topo_sort(tool_ids: list[str], by_id: dict[str, dict[str, Any]]) -> list[str]:
    pending = list(tool_ids)
    resolved: list[str] = []
    remaining = set(pending)
    guard = 0
    while pending:
        guard += 1
        if guard > 200:
            raise ValueError("Dependency cycle while ordering installs")
        progressed = False
        next_pending: list[str] = []
        for tid in pending:
            deps = [d for d in (by_id.get(tid, {}).get("depends_on") or []) if d in remaining]
            if deps:
                next_pending.append(tid)
                continue
            resolved.append(tid)
            remaining.discard(tid)
            progressed = True
        if not progressed:
            resolved.extend(next_pending)
            break
        pending = next_pending
    return resolved
