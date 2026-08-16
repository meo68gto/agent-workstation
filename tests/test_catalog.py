#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("AGENT_WORKSTATION_REPO", str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from workstation.catalog import (  # noqa: E402
    apt_packages_for,
    load_debian_map,
    load_source_lock,
    load_tools,
    path_aliases_for,
    resolve_profile,
    topo_sort,
    tools_by_id,
)


class CatalogTests(unittest.TestCase):
    def test_exactly_fifty_sequential_tools(self) -> None:
        tools = load_tools(ROOT)
        self.assertEqual(len(tools), 50)
        self.assertEqual([t["number"] for t in tools], list(range(1, 51)))

    def test_core_profile_has_seventeen_required(self) -> None:
        profile = resolve_profile("core", tools=load_tools(ROOT))
        self.assertEqual(len(profile["required"]), 17)
        self.assertIn("python", profile["required"])
        self.assertIn("just", profile["required"])

    def test_developer_extends_core(self) -> None:
        profile = resolve_profile("developer", tools=load_tools(ROOT))
        self.assertIn("python", profile["required"])
        self.assertIn("git", profile["required"])
        self.assertIn("go", profile["required"])
        self.assertIn("rust", profile["required"])

    def test_all_profile_is_full_catalog(self) -> None:
        tools = load_tools(ROOT)
        profile = resolve_profile("all", tools=tools)
        self.assertEqual(len(profile["required"]), 50)

    def test_unknown_profile(self) -> None:
        with self.assertRaises(KeyError):
            resolve_profile("not-a-profile", tools=load_tools(ROOT))

    def test_debian_fd_and_bat_aliases(self) -> None:
        tools = tools_by_id(load_tools(ROOT))
        debian = load_debian_map(ROOT)
        self.assertEqual(apt_packages_for(tools["fd"], debian), ["fd-find"])
        self.assertEqual(apt_packages_for(tools["delta"], debian), ["git-delta"])
        self.assertEqual(path_aliases_for(tools["fd"], debian), [{"from": "fdfind", "to": "fd"}])
        self.assertEqual(path_aliases_for(tools["bat"], debian), [{"from": "batcat", "to": "bat"}])

    def test_source_lock_covers_core_official_releases(self) -> None:
        lock = load_source_lock(ROOT)
        for tool_id in ("uv", "node", "pnpm", "yq", "just"):
            artifacts = lock["tools"][tool_id]["artifacts"]
            for arch in ("linux-amd64", "linux-arm64"):
                self.assertIn(arch, artifacts, msg=f"{tool_id} {arch}")
                self.assertTrue(artifacts[arch]["url"].startswith("https://"))
                self.assertEqual(len(artifacts[arch]["sha256"]), 64)
        self.assertIn("gh", lock["apt_repositories"])

    def test_topo_sort_puts_node_before_pnpm(self) -> None:
        tools = load_tools(ROOT)
        ordered = topo_sort(["pnpm", "node", "uv"], tools_by_id(tools))
        self.assertLess(ordered.index("node"), ordered.index("pnpm"))


if __name__ == "__main__":
    unittest.main()
