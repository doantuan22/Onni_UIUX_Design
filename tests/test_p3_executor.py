"""P3 DO: controlled editing — scope lock, preservation, business-logic and framework guards."""
from __future__ import annotations

import unittest

import _paths  # noqa: F401
from test_p2_reasoning import KNOWLEDGE, PRESERVATION, REPO, make_plan
from uiux.engine.executor.execution_gate import check_execution_gate
from uiux.engine.executor.executor import ChunkExecutor
from uiux.engine.executor.recipe_adapter import RecipeAdapter

CHECKOUT = "src/components/Checkout.tsx"


def edit(executor, content, file=CHECKOUT, component="Checkout", chunk="chunk_0"):
    return executor.editor.apply_edit(
        chunk_id=chunk, target_file=file, target_component=component,
        operation="modify", reason="test", new_content=content,
    )


class ExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = make_plan()
        self.executor = ChunkExecutor(self.plan, framework="react-tailwind")

    def test_valid_edit_is_ledgered(self) -> None:
        result = edit(self.executor, "<div className='p-4'>ok</div>")
        self.assertTrue(result["success"])
        self.assertEqual(result["ledger_entry"]["scope_status"], "within_scope")

    def test_out_of_scope_file_yields_scope_deviation(self) -> None:
        result = edit(self.executor, "<nav/>", file="src/components/GlobalNav.tsx", component="GlobalNav")
        self.assertFalse(result["success"])
        self.assertEqual(result["deviation"]["type"], "scope_expansion")

    def test_locked_palette_edit_yields_strategy_deviation(self) -> None:
        result = edit(self.executor, "theme.colors.primary = '#FF0000'")
        self.assertFalse(result["success"])
        self.assertEqual(result["deviation"]["type"], "strategy_change")

    def test_business_logic_in_ui_is_rejected(self) -> None:
        result = edit(self.executor, "const u = db.query('SELECT * FROM users')")
        self.assertFalse(result["success"])
        self.assertEqual(result["deviation"]["type"], "architecture_conflict")

    def test_nextjs_client_hook_without_directive_is_rejected(self) -> None:
        plan = make_plan(repo_profile={"framework": {"name": "nextjs"}, "files": [CHECKOUT]})
        executor = ChunkExecutor(plan, framework="nextjs")
        result = edit(executor, "import { useState } from 'react';\nfunction C(){ const [a]=useState(); return <div/>; }")
        self.assertFalse(result["success"])
        self.assertEqual(result["deviation"]["affected_scope"], "framework_conventions")

    def test_recipe_adapter_maps_repository_tokens(self) -> None:
        adapted = RecipeAdapter(self.plan).adapt_recipe(
            "<div class='bg-brand-500 p-4 text-neutral-900'>Hello</div>", {"brand": "primary", "neutral": "slate"})
        self.assertIn("bg-primary-500", adapted)
        self.assertIn("text-slate-900", adapted)

    def test_report_is_driven_by_ledger_not_assumed(self) -> None:
        report = self.executor.execute_plan()
        self.assertEqual(report["status"], "PARTIAL")
        self.assertFalse(report["ready_for_p4"])
        self.assertEqual(report["chunks_applied"], [])
        self.assertTrue(report["chunks_pending"])

    def test_all_chunks_edited_is_ready_for_p4(self) -> None:
        edits = [
            {"chunk_id": c["id"], "target_file": CHECKOUT, "target_component": "Checkout",
             "operation": "modify", "reason": "test", "new_content": "<div className='p-4'/>"}
            for c in self.plan["execution_chunks"]
        ]
        report = self.executor.execute_plan(edits=edits)
        self.assertEqual(report["status"], "COMPLETED")
        self.assertTrue(report["ready_for_p4"])
        self.assertEqual(report["deviations"], [])
        self.assertEqual(report["files_modified"], [CHECKOUT])

    def test_rejected_edit_makes_report_deviated(self) -> None:
        edits = [{"chunk_id": "chunk_0", "target_file": "src/components/GlobalNav.tsx",
                  "target_component": "GlobalNav", "operation": "modify", "reason": "t", "new_content": "<nav/>"}]
        report = self.executor.execute_plan(edits=edits)
        self.assertEqual(report["status"], "DEVIATED")
        self.assertFalse(report["ready_for_p4"])
        self.assertEqual(report["chunks_failed"], ["chunk_0"])

    def test_scope_lock_requires_exact_paths(self) -> None:
        for path in ("src/components/Checkout.tsx.bak", "", "src"):
            self.assertFalse(self.executor.scope_lock.is_file_allowed(path), path)
        self.assertTrue(self.executor.scope_lock.is_file_allowed("./src/components/Checkout.tsx"))


class ExecutionGateTests(unittest.TestCase):
    def test_gate_passes_for_ready_plan(self) -> None:
        self.assertEqual(check_execution_gate(make_plan())["status"], "PASS")

    def test_gate_blocks_when_planning_gate_is_blocked(self) -> None:
        plan = make_plan(repo_profile={})
        self.assertEqual(check_execution_gate(plan)["status"], "BLOCKED")
        report = ChunkExecutor(plan).execute_plan()
        self.assertFalse(report["ready_for_p4"])


if __name__ == "__main__":
    unittest.main()
