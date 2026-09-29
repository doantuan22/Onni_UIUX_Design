"""Knowledge registry and tool registry."""
from __future__ import annotations

import unittest

import _paths  # noqa: F401
from uiux import api
from uiux.knowledge import catalog, registry

ENTRIES, _ = catalog.load()


class KnowledgeRegistryTests(unittest.TestCase):
    def test_registry_is_fresh_and_covers_every_collection(self) -> None:
        self.assertEqual(catalog.check(), [])
        counts = registry.collections()
        for collection in registry.COLLECTIONS:
            self.assertGreater(counts.get(collection, 0), 0, collection)
        documents = len(catalog.component_documents())
        self.assertEqual(sum(counts.values()) - documents, len(ENTRIES))

    def test_query_filters(self) -> None:
        styles = registry.query(collection="styles")
        self.assertEqual({r["kind"] for r in styles}, {"style"})
        m5 = registry.query(collection="motion", category="M5")
        self.assertTrue(m5 and all(r["category"] == "M5" for r in m5))
        self.assertTrue(any(r["id"] == "style.calm-futurism" for r in registry.query(text="calm")))
        self.assertEqual([r["id"] for r in registry.query(ids=["effect.glow"])], ["effect.glow"])

    def test_unknown_ids_and_collections_fail_loudly(self) -> None:
        with self.assertRaises(registry.KnowledgeLookupError):
            registry.query(ids=["style.does-not-exist"])
        with self.assertRaises(registry.KnowledgeLookupError):
            registry.query(collection="colours")

    def test_get_returns_parsed_entry_without_knowing_the_file(self) -> None:
        entry = registry.get("layout.hero-dashboard")
        self.assertEqual(entry["kind"], "layout")
        self.assertEqual(entry, {**ENTRIES["layout.hero-dashboard"]})

    def test_components_are_documents(self) -> None:
        doc = registry.get("component.forms-controls")
        self.assertEqual(doc["collection"], "components")
        self.assertIn("# Form and control grammar", doc["content"])

    def test_api_retrieve_knowledge(self) -> None:
        result = api.retrieve_knowledge(collection="recipes", include_content=True)
        self.assertEqual(result["count"], 16)
        self.assertTrue(all(row["content"].startswith("id: recipe.") for row in result["entries"]))


class ToolRegistryTests(unittest.TestCase):
    REQUIRED = {"resolve_capabilities", "retrieve_knowledge", "resolve_technology", "analyze_design_quality",
                "run_runtime", "run_evals", "validate_skill"}

    def test_required_tools_and_metadata(self) -> None:
        tools = api.list_tools()
        self.assertLessEqual(self.REQUIRED, {t["id"] for t in tools})
        for tool in tools:
            with self.subTest(tool=tool["id"]):
                for key in ("id", "description", "entrypoint", "input", "output", "dependencies", "runtime_requirements"):
                    self.assertIn(key, tool)
                module, _, function = tool["entrypoint"].partition(":")
                self.assertEqual(module, "uiux.api")
                self.assertIn(function, api.__all__)
                self.assertTrue(callable(getattr(api, function)))

    def test_call_tool_validates_parameters(self) -> None:
        with self.assertRaises(api.ToolError):
            api.call_tool("does-not-exist")
        with self.assertRaises(api.ToolError):
            api.call_tool("resolve_capabilities", {})
        with self.assertRaises(api.ToolError):
            api.call_tool("retrieve_knowledge", {"colour": "red"})

    def test_call_tool_dispatches(self) -> None:
        tech = api.call_tool("resolve_technology", {"capabilities": ["motion.m1-hover"]})
        self.assertEqual(tech["assignments"]["motion.m1-hover"]["technology"], "tech.css")
        evals = api.call_tool("run_evals", {"suites": ["knowledge", "quality-fixtures"]})
        self.assertEqual(evals["status"], "PASS", evals)
        manual = api.call_tool("run_evals", {"suites": ["scenarios"], "scenario_ids": ["E01", "E80"]})
        self.assertEqual(manual["status"], "MANUAL")
        self.assertEqual([s["id"] for s in manual["suites"]["scenarios"]["scenarios"]], ["E01", "E80"])


if __name__ == "__main__":
    unittest.main()
