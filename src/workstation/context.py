"""Runtime context shared by doctor, bootstrap, and repair."""

from __future__ import annotations

import os
import platform
import pwd
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "0") == "1"


def repo_root() -> Path:
    return Path(os.environ.get("AGENT_WORKSTATION_REPO", Path(__file__).resolve().parents[2]))


def state_root() -> Path:
    return Path(
        os.environ.get(
            "AGENT_WORKSTATION_STATE",
            Path.home() / ".local" / "state" / "agent-workstation",
        )
    )


def run_id() -> str:
    return os.environ.get(
        "AGENT_WORKSTATION_RUN_ID",
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    )


def profile_name() -> str:
    return os.environ.get("AGENT_WORKSTATION_PROFILE", "core")


def tool_filter() -> str:
    return os.environ.get("AGENT_WORKSTATION_TOOL", "")


def operation() -> str:
    return os.environ.get("AGENT_WORKSTATION_OPERATION", "bootstrap")


def dry_run() -> bool:
    return _env_flag("AGENT_WORKSTATION_DRY_RUN")


def json_mode() -> bool:
    return _env_flag("AGENT_WORKSTATION_JSON")


def verbose() -> bool:
    return _env_flag("AGENT_WORKSTATION_VERBOSE")


def no_sudo() -> bool:
    return _env_flag("AGENT_WORKSTATION_NO_SUDO")


def repair_flag() -> bool:
    return _env_flag("AGENT_WORKSTATION_REPAIR")


def target_user() -> str:
    return os.environ.get("AGENT_WORKSTATION_TARGET_USER") or _current_user()


def _current_user() -> str:
    try:
        return pwd.getpwuid(os.geteuid()).pw_name
    except Exception:
        return os.environ.get("USER", "unknown")


def target_home() -> Path:
    user = target_user()
    try:
        return Path(pwd.getpwnam(user).pw_dir)
    except Exception:
        return Path.home()


def user_bin() -> Path:
    return target_home() / ".local" / "bin"


def system_prefix() -> Path:
    return Path("/usr/local")


def privileged() -> bool:
    return os.geteuid() == 0


def can_sudo() -> bool:
    if no_sudo():
        return False
    if privileged():
        return True
    sudo = shutil.which("sudo")
    if not sudo:
        return False
    try:
        r = subprocess.run([sudo, "-n", "true"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def log(level: str, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] [{level}] {msg}", file=sys.stderr)


def detect_host() -> dict[str, Any]:
    return {
        "hostname": platform.node(),
        "os": platform.system().lower(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "distro": _detect_distro(),
        "debian_like": is_debian_like(),
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


def is_debian_like() -> bool:
    if Path("/etc/debian_version").exists():
        return True
    try:
        with open("/etc/os-release") as f:
            text = f.read().lower()
        return "debian" in text or "ubuntu" in text
    except Exception:
        return False


def arch_key() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "linux-amd64"
    if machine in {"aarch64", "arm64"}:
        return "linux-arm64"
    return f"linux-{machine}"


def dpkg_arch() -> str:
    if arch_key() == "linux-arm64":
        return "arm64"
    return "amd64"


def ensure_process_path() -> list[str]:
    """Prepend install destinations so doctor sees freshly installed tools."""
    extras = [str(user_bin()), str(system_prefix() / "bin")]
    current = os.environ.get("PATH", "")
    parts = [p for p in extras if p]
    for item in current.split(":"):
        if item and item not in parts:
            parts.append(item)
    os.environ["PATH"] = ":".join(parts)
    return parts
