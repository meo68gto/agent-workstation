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
    load_stack_tools,
    load_tools_for_profile,
    resolve_profile,
)
from workstation.install import install_missing  # noqa: E402


class AgentStackTests(unittest.TestCase):
    def test_eight_tools_and_known_licenses(self) -> None:
        tools = load_stack_tools(ROOT)
        self.assertEqual(len(tools), 8)
        by_id = {t["id"]: t for t in tools}
        self.assertEqual(by_id["browser-use"]["license"]["expression"], "MIT")
        self.assertEqual(by_id["mem0"]["license"]["expression"], "Apache-2.0")
        self.assertEqual(by_id["langgraph"]["license"]["expression"], "MIT")
        self.assertEqual(by_id["pydantic-ai"]["license"]["expression"], "MIT")
        self.assertEqual(by_id["crewai"]["license"]["expression"], "MIT")
        self.assertEqual(by_id["firecrawl"]["license"]["expression"], "AGPL-3.0-only")
        self.assertEqual(by_id["firecrawl"]["license"]["classification"], "copyleft")
        self.assertTrue(by_id["firecrawl"]["install"].get("agpl_ack_required"))

    def test_profile_uses_second_catalog(self) -> None:
        profile = resolve_profile("agent-stack")
        self.assertEqual(profile["catalog"], "agent-stack")
        tools = load_tools_for_profile(profile, ROOT)
        self.assertEqual({t["id"] for t in tools}, {
            "langfuse", "pydantic-ai", "langgraph", "mem0",
            "browser-use", "crewai", "firecrawl", "mastra",
        })
        self.assertIn("pydantic-ai", profile["required"])
        self.assertNotIn("git", profile["required"])

    def test_primary_catalog_unchanged(self) -> None:
        profile = resolve_profile("core")
        self.assertEqual(profile.get("catalog", "primary"), "primary")
        self.assertEqual(len(profile["required"]), 17)

    def test_dry_run_plans_uv_pip_and_blocks_docker(self) -> None:
        profile = resolve_profile("agent-stack")
        tools = load_tools_for_profile(profile, ROOT)
        results = install_missing(tools, profile["required"], {}, dry=True)
        by_id = {r["id"]: r for r in results}
        self.assertEqual(by_id["pydantic-ai"]["status"], "planned")
        self.assertEqual(by_id["pydantic-ai"]["strategy"], "uv-pip")
        self.assertEqual(by_id["langgraph"]["strategy"], "uv-pip")

    def test_outline_file_exists(self) -> None:
        text = (ROOT / "prompts" / "productionize-agent-stack.md").read_text()
        self.assertIn("browser-use", text)
        self.assertIn("Langfuse", text)
        self.assertIn("Firecrawl", text)


if __name__ == "__main__":
    unittest.main()
