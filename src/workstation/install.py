"""Install adapters for apt, official apt repos, and official releases."""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .catalog import apt_packages_for, load_source_lock, topo_sort, tools_by_id
from .context import (
    arch_key,
    can_sudo,
    dpkg_arch,
    is_debian_like,
    log,
    no_sudo,
    privileged,
    state_root,
    system_prefix,
    user_bin,
    verbose,
)


SUPPORTED_STRATEGIES = {"apt", "official_release", "official_apt_repository", "uv-pip"}


class InstallError(RuntimeError):
    pass


def _run(argv: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    log("INFO", "exec: " + " ".join(argv))
    return subprocess.run(argv, capture_output=not verbose(), text=True, env=env)


def _maybe_sudo(argv: list[str]) -> list[str]:
    if privileged():
        return argv
    if no_sudo():
        raise InstallError("privileged operation required but --no-sudo was set")
    if not shutil.which("sudo"):
        raise InstallError("sudo is required but not available")
    return ["sudo", *argv]


def _require_sudo_ok(tool: dict[str, Any]) -> None:
    if tool.get("install", {}).get("requires_sudo") and not (privileged() or can_sudo()):
        raise InstallError("requires sudo, which is not available")


def download(url: str, dest: Path, sha256: str | None = None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if sha256:
        sha256 = str(sha256).strip()
    if dest.exists() and sha256:
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        if digest == sha256:
            return dest
        dest.unlink()
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"}:
        raise InstallError(f"refusing non-http URL: {url}")
    log("INFO", f"download {url}")
    with urllib.request.urlopen(url, timeout=120) as resp, dest.open("wb") as fh:  # noqa: S310
        shutil.copyfileobj(resp, fh)
    if sha256:
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        if digest != sha256:
            dest.unlink(missing_ok=True)
            raise InstallError(f"sha256 mismatch for {dest.name}: got {digest}, expected {sha256}")
    return dest


def _copy_binary(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_prefix(tool: dict[str, Any]) -> Path:
    if tool.get("install", {}).get("requires_sudo") and (privileged() or can_sudo()):
        return system_prefix()
    return user_bin().parent  # ~/.local


def bin_dir_for(tool: dict[str, Any]) -> Path:
    prefix = install_prefix(tool)
    if prefix == user_bin().parent:
        return user_bin()
    return prefix / "bin"


def artifact_for(tool_id: str, lock: dict[str, Any]) -> dict[str, Any]:
    tool_lock = (lock.get("tools") or {}).get(tool_id)
    if not tool_lock:
        raise InstallError(f"{tool_id} missing from source lock")
    key = arch_key()
    artifact = (tool_lock.get("artifacts") or {}).get(key)
    if not artifact:
        raise InstallError(f"{tool_id} has no locked artifact for {key}")
    return {**tool_lock, **artifact, "arch": key}


def install_pnpm_corepack(lock: dict[str, Any], dry: bool) -> dict[str, Any]:
    version = ((lock.get("tools") or {}).get("pnpm") or {}).get("version")
    if not version:
        raise InstallError("pnpm version missing from source lock")
    if dry:
        return {
            "status": "planned",
            "strategy": "official_release",
            "reason": f"would activate pnpm {version} via corepack",
            "version": version,
        }
    corepack = shutil.which("corepack")
    if not corepack:
        raise InstallError("corepack not on PATH; install node first")
    env = os.environ.copy()
    env["COREPACK_ENABLE_DOWNLOAD_PROMPT"] = "0"
    enable = _run([corepack, "enable"], env=env)
    if enable.returncode != 0:
        raise InstallError(f"corepack enable failed: {(enable.stderr or enable.stdout or '')[-300:]}")
    prepare = _run([corepack, "prepare", f"pnpm@{version}", "--activate"], env=env)
    if prepare.returncode != 0:
        raise InstallError(f"corepack prepare pnpm@{version} failed: {(prepare.stderr or prepare.stdout or '')[-300:]}")
    return {
        "status": "installed",
        "strategy": "official_release",
        "reason": f"activated pnpm {version} via corepack",
        "version": version,
        "path": shutil.which("pnpm"),
    }


def install_official_release(tool: dict[str, Any], lock: dict[str, Any], dry: bool) -> dict[str, Any]:
    if tool["id"] == "pnpm" or ((lock.get("tools") or {}).get(tool["id"]) or {}).get("method") == "corepack":
        return install_pnpm_corepack(lock, dry)
    artifact = artifact_for(tool["id"], lock)
    dest_bin = bin_dir_for(tool)
    if dry:
        return {
            "status": "planned",
            "strategy": "official_release",
            "reason": f"would install {tool['id']} {artifact.get('version')} -> {dest_bin}",
            "version": artifact.get("version"),
            "url": artifact.get("url"),
        }
    if platform.system().lower() != "linux":
        raise InstallError("official_release artifacts are Linux-only")
    if tool.get("install", {}).get("requires_sudo"):
        _require_sudo_ok(tool)

    cache = state_root() / "cache" / "downloads"
    filename = Path(urlparse(artifact["url"]).path).name
    archive = download(artifact["url"], cache / filename, artifact.get("sha256"))

    with tempfile.TemporaryDirectory(prefix="aw-extract-") as tmp:
        tmp_path = Path(tmp)
        if artifact.get("prefix"):
            _extract(archive, tmp_path, strip=int(artifact.get("strip_components") or 1))
            prefix = install_prefix(tool)
            _install_tree(tmp_path, prefix, tool)
        elif artifact.get("tree"):
            dest_tree = install_prefix(tool) / "lib" / "agent-workstation" / tool["id"]
            _extract(archive, tmp_path, strip=int(artifact.get("strip_components") or 0))
            if dest_tree.exists():
                shutil.rmtree(dest_tree)
            dest_tree.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(tmp_path, dest_tree)
            dest_bin.mkdir(parents=True, exist_ok=True)
            for name in list(artifact.get("binaries") or [tool["id"]]):
                src = _find_member(dest_tree, name)
                src.chmod(src.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                dest = dest_bin / name
                if dest.is_symlink() or dest.exists():
                    dest.unlink()
                os.symlink(src, dest)
        elif artifact.get("rename"):
            # single downloaded file
            dest = dest_bin / artifact["rename"]
            if privileged() or not tool.get("install", {}).get("requires_sudo"):
                dest_bin.mkdir(parents=True, exist_ok=True)
                _copy_binary(archive, dest)
            else:
                _require_sudo_ok(tool)
                _run(_maybe_sudo(["install", "-m", "0755", "-D", str(archive), str(dest)]))
        else:
            _extract(archive, tmp_path, strip=int(artifact.get("strip_components") or 0))
            binaries = list(artifact.get("binaries") or [tool["id"]])
            dest_bin.mkdir(parents=True, exist_ok=True)
            for name in binaries:
                src = _find_member(tmp_path, name)
                dest = dest_bin / name
                if dest_bin == user_bin() or privileged():
                    _copy_binary(src, dest)
                else:
                    _run(_maybe_sudo(["install", "-m", "0755", "-D", str(src), str(dest)]))

    return {
        "status": "installed",
        "strategy": "official_release",
        "reason": f"installed {tool['id']} {artifact.get('version')} to {dest_bin}",
        "version": artifact.get("version"),
        "path": str(dest_bin / tool["id"]),
    }


def _extract(archive: Path, dest: Path, strip: int = 0) -> None:
    mode = "r:*"
    with tarfile.open(archive, mode) as tar:
        def safe(member: tarfile.TarInfo) -> tarfile.TarInfo | None:
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts:
                return None
            if strip:
                parts = name.parts[strip:]
                if not parts:
                    return None
                member.name = str(Path(*parts))
            return member

        members = []
        for member in tar.getmembers():
            filtered = safe(member)
            if filtered is not None:
                members.append(filtered)
        try:
            tar.extractall(dest, members=members, filter="data")
        except TypeError:
            tar.extractall(dest, members=members)


def _find_member(root: Path, name: str) -> Path:
    direct = root / name
    if direct.is_file():
        return direct
    matches = [p for p in root.rglob(name) if p.is_file() and p.name == name]
    if not matches:
        raise InstallError(f"archive did not contain {name}")
    return matches[0]


def _install_tree(src: Path, prefix: Path, tool: dict[str, Any]) -> None:
    """Copy a prefix-style release (Node) into /usr/local or ~/.local."""
    use_sudo = tool.get("install", {}).get("requires_sudo") and not privileged()
    for sub in ("bin", "lib", "include", "share"):
        src_sub = src / sub
        if not src_sub.exists():
            continue
        dest_sub = prefix / sub
        if use_sudo:
            _run(_maybe_sudo(["mkdir", "-p", str(dest_sub)]))
            _run(_maybe_sudo(["cp", "-a", f"{src_sub}/.", str(dest_sub)]))
        else:
            dest_sub.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_sub, dest_sub, dirs_exist_ok=True, symlinks=True)


def install_apt_packages(packages: list[str], dry: bool) -> dict[str, Any]:
    if not packages:
        return {"status": "skipped", "strategy": "apt", "reason": "no packages", "packages": []}
    if dry:
        return {
            "status": "planned",
            "strategy": "apt",
            "reason": f"would apt-get install {' '.join(packages)}",
            "packages": packages,
        }
    if not is_debian_like() or not shutil.which("apt-get"):
        raise InstallError("apt strategy requires a Debian-like host with apt-get")
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    update = _run(_maybe_sudo(["apt-get", "update", "-qq"]), env=env)
    if update.returncode != 0:
        raise InstallError(f"apt-get update failed: {update.stderr[-400:] if update.stderr else update.returncode}")
    install = _run(
        _maybe_sudo(
            ["apt-get", "install", "-y", "-qq", "--no-install-recommends", *packages]
        ),
        env=env,
    )
    if install.returncode != 0:
        raise InstallError(f"apt-get install failed: {install.stderr[-400:] if install.stderr else install.returncode}")
    return {
        "status": "installed",
        "strategy": "apt",
        "reason": f"installed {', '.join(packages)}",
        "packages": packages,
    }


def install_official_apt_repo(tool: dict[str, Any], lock: dict[str, Any], dry: bool) -> dict[str, Any]:
    repo = (lock.get("apt_repositories") or {}).get(tool["id"])
    if not repo:
        raise InstallError(f"no apt repository lock for {tool['id']}")
    packages = list(repo.get("packages") or [tool["id"]])
    if dry:
        return {
            "status": "planned",
            "strategy": "official_apt_repository",
            "reason": f"would add repo and install {packages}",
            "packages": packages,
        }
    if not is_debian_like():
        raise InstallError("official_apt_repository requires Debian")
    _require_sudo_ok(tool)
    key_url = repo["key_url"]
    keyring = Path(repo["keyring_path"])
    list_path = Path(repo["list_path"])
    source_line = str(repo["source_line"]).format(arch=dpkg_arch())

    cache = state_root() / "cache" / "downloads"
    key_file = download(key_url, cache / Path(key_url).name)

    _run(_maybe_sudo(["mkdir", "-p", "-m", "755", str(keyring.parent)]))
    _run(_maybe_sudo(["install", "-m", "0644", str(key_file), str(keyring)]))
    with tempfile.NamedTemporaryFile("w", delete=False, prefix="aw-src-") as tmp:
        tmp.write(source_line + "\n")
        tmp_path = tmp.name
    try:
        _run(_maybe_sudo(["install", "-m", "0644", tmp_path, str(list_path)]))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return install_apt_packages(packages, dry=False)


def stack_venv_python() -> Path:
    return state_root() / "venvs" / "agent-stack" / "bin" / "python"


def ensure_stack_venv() -> Path:
    py = stack_venv_python()
    if py.exists():
        return py
    venv = py.parent.parent
    venv.parent.mkdir(parents=True, exist_ok=True)
    uv = shutil.which("uv")
    if uv:
        created = _run([uv, "venv", str(venv)])
        if created.returncode != 0:
            raise InstallError(f"uv venv failed: {(created.stderr or '')[-300:]}")
    else:
        created = _run([sys.executable, "-m", "venv", str(venv)])
        if created.returncode != 0:
            raise InstallError(f"python -m venv failed: {(created.stderr or '')[-300:]}")
    if not py.exists():
        raise InstallError(f"venv python missing after create: {py}")
    return py


def install_uv_pip(tool: dict[str, Any], dry: bool) -> dict[str, Any]:
    package = (tool.get("install") or {}).get("package") or tool["id"]
    if dry:
        return {
            "status": "planned",
            "strategy": "uv-pip",
            "reason": f"would uv-pip install {package} into agent-stack venv",
            "package": package,
        }
    py = ensure_stack_venv()
    uv = shutil.which("uv")
    if uv:
        cmd = [uv, "pip", "install", "--python", str(py), package]
    else:
        cmd = [str(py), "-m", "pip", "install", package]
    result = _run(cmd)
    if result.returncode != 0:
        raise InstallError(f"install {package} failed: {(result.stderr or result.stdout or '')[-400:]}")
    return {
        "status": "installed",
        "strategy": "uv-pip",
        "reason": f"installed {package} into {py.parent.parent}",
        "package": package,
        "path": str(py),
    }


def install_one(
    tool: dict[str, Any],
    lock: dict[str, Any],
    debian_map: dict[str, Any],
    dry: bool,
) -> dict[str, Any]:
    strategy = (tool.get("install") or {}).get("preferred_strategy")
    if strategy not in SUPPORTED_STRATEGIES:
        return {
            "id": tool["id"],
            "status": "blocked",
            "strategy": strategy,
            "reason": f"no adapter for strategy {strategy}",
        }
    try:
        if strategy == "apt":
            result = install_apt_packages(apt_packages_for(tool, debian_map), dry)
        elif strategy == "official_apt_repository":
            result = install_official_apt_repo(tool, lock, dry)
        elif strategy == "uv-pip":
            result = install_uv_pip(tool, dry)
        else:
            result = install_official_release(tool, lock, dry)
        result["id"] = tool["id"]
        return result
    except InstallError as exc:
        return {
            "id": tool["id"],
            "status": "failed",
            "strategy": strategy,
            "reason": str(exc),
        }


def install_missing(
    tools: list[dict[str, Any]],
    missing_ids: list[str],
    debian_map: dict[str, Any],
    dry: bool = False,
) -> list[dict[str, Any]]:
    if not missing_ids:
        return []
    lock = load_source_lock()
    by_id = tools_by_id(tools)
    ordered = topo_sort(missing_ids, by_id)
    results: list[dict[str, Any]] = []

    apt_ids = [
        tid
        for tid in ordered
        if (by_id.get(tid, {}).get("install") or {}).get("preferred_strategy") == "apt"
    ]
    other_ids = [tid for tid in ordered if tid not in apt_ids]

    if apt_ids:
        packages: list[str] = []
        for tid in apt_ids:
            packages.extend(apt_packages_for(by_id[tid], debian_map))
        # de-dupe, keep order
        seen: set[str] = set()
        unique = []
        for pkg in packages:
            if pkg not in seen:
                seen.add(pkg)
                unique.append(pkg)
        try:
            batched = install_apt_packages(unique, dry)
            for tid in apt_ids:
                results.append({**batched, "id": tid, "packages": apt_packages_for(by_id[tid], debian_map)})
        except InstallError as exc:
            for tid in apt_ids:
                results.append(
                    {
                        "id": tid,
                        "status": "failed",
                        "strategy": "apt",
                        "reason": str(exc),
                    }
                )

    for tid in other_ids:
        results.append(install_one(by_id[tid], lock, debian_map, dry))
    return results
