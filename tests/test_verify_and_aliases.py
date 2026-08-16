#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("AGENT_WORKSTATION_REPO", str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from workstation.aliases import apply_aliases, plan_aliases  # noqa: E402
from workstation.catalog import load_debian_map, load_tools, tools_by_id  # noqa: E402
from workstation.verify import verify_tool  # noqa: E402


class VerifyTests(unittest.TestCase):
    def test_exec_uses_catalog_argv_not_bare_which(self) -> None:
        tool = {
            "id": "fd",
            "commands": {"primary": ["fd"], "alternatives": ["fdfind"]},
            "verify": [{"id": "version", "type": "exec", "argv": ["fd", "--version"]}],
        }
        with mock.patch("workstation.verify.run_exec") as run_exec:
            run_exec.return_value = {
                "ok": False,
                "reason": "fd not on PATH",
                "output": "",
                "path": None,
            }
            result = verify_tool(tool)
        run_exec.assert_called_once_with(["fd", "--version"])
        self.assertEqual(result.status, "failed")

    def test_python_import_contract(self) -> None:
        tool = {
            "id": "pandas",
            "commands": {"primary": []},
            "verify": [{"id": "import", "type": "python", "code": "print('ok')"}],
        }
        result = verify_tool(tool)
        self.assertEqual(result.status, "passed")

    def test_http_contains_rejects_wrong_service(self) -> None:
        from workstation.verify import run_http

        class FakeResp:
            status = 200

            def read(self, _n: int) -> bytes:
                return b"<html>next app</html>"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with mock.patch("workstation.verify.urlopen", return_value=FakeResp()):
            info = run_http("http://127.0.0.1:3000/api/public/health", contains="status")
        self.assertFalse(info["ok"])
        self.assertIn("did not contain", info["reason"])

    def test_http_only_is_not_configured(self) -> None:
        tool = {
            "id": "n8n",
            "commands": {"primary": []},
            "verify": [{"id": "health", "type": "http", "url": "http://127.0.0.1:1/healthz"}],
        }
        result = verify_tool(tool)
        self.assertEqual(result.status, "not_configured")

    def test_tmux_uses_dash_v(self) -> None:
        tool = {
            "id": "tmux",
            "commands": {"primary": ["tmux"]},
            "verify": [{"id": "version", "type": "exec", "argv": ["tmux", "-V"]}],
        }
        with mock.patch("workstation.verify.run_exec") as run_exec:
            run_exec.return_value = {"ok": True, "reason": "ok", "output": "tmux 3.5", "path": "/usr/bin/tmux"}
            result = verify_tool(tool)
        run_exec.assert_called_once_with(["tmux", "-V"])
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.version, "tmux 3.5")


class AliasTests(unittest.TestCase):
    def test_creates_shim_and_refuses_to_replace_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "fdfind"
            source.write_text("#!/bin/sh\necho fd\n")
            source.chmod(0o755)
            dest_dir = tmp_path / "bin"
            dest_dir.mkdir()
            plan = [
                {
                    "id": "fd",
                    "from": "fdfind",
                    "to": "fd",
                    "source": str(source),
                    "dest": str(dest_dir / "fd"),
                }
            ]
            created = apply_aliases(plan, dry=False)
            self.assertEqual(created[0]["status"], "created")
            self.assertTrue((dest_dir / "fd").is_symlink())

            real = dest_dir / "bat"
            real.write_text("real")
            blocked = apply_aliases(
                [
                    {
                        "id": "bat",
                        "from": "batcat",
                        "to": "bat",
                        "source": str(source),
                        "dest": str(real),
                    }
                ],
                dry=False,
            )
            self.assertEqual(blocked[0]["status"], "blocked")
            self.assertEqual(real.read_text(), "real")

    def test_plan_includes_core_aliases(self) -> None:
        tools = load_tools(ROOT)
        debian = load_debian_map(ROOT)
        wanted = tools_by_id(tools)
        planned = plan_aliases([wanted["fd"], wanted["bat"]], debian, dest_dir=Path("/tmp/bin"))
        targets = {(p["from"], p["to"]) for p in planned}
        self.assertIn(("fdfind", "fd"), targets)
        self.assertIn(("batcat", "bat"), targets)


if __name__ == "__main__":
    unittest.main()
