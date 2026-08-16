#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("AGENT_WORKSTATION_REPO", str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from workstation.catalog import load_debian_map, load_tools, resolve_profile  # noqa: E402
from workstation.install import install_missing  # noqa: E402


class InstallPlanTests(unittest.TestCase):
    def test_dry_run_core_plans_apt_and_locked_releases(self) -> None:
        tools = load_tools(ROOT)
        debian = load_debian_map(ROOT)
        profile = resolve_profile("core", tools=tools)
        results = install_missing(tools, profile["required"], debian, dry=True)
        by_id = {r["id"]: r for r in results}
        self.assertIn("git", by_id)
        self.assertEqual(by_id["git"]["status"], "planned")
        self.assertEqual(by_id["git"]["strategy"], "apt")
        self.assertIn("git-delta", by_id["delta"]["reason"] + str(by_id["delta"].get("packages")))
        self.assertEqual(by_id["uv"]["strategy"], "official_release")
        self.assertTrue(str(by_id["uv"].get("url", "")).startswith("https://"))
        self.assertEqual(by_id["gh"]["strategy"], "official_apt_repository")
        self.assertEqual(by_id["node"]["strategy"], "official_release")

    def test_unknown_strategy_is_blocked(self) -> None:
        tools = [
            {
                "id": "n8n",
                "install": {"preferred_strategy": "docker-compose", "requires_sudo": True},
                "depends_on": [],
            }
        ]
        results = install_missing(tools, ["n8n"], {}, dry=True)
        self.assertEqual(results[0]["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
