"""P3/P4 are reachable as public tools and chain: plan_modification -> guard_edits -> verify_implementation."""
from __future__ import annotations

import unittest

import _paths  # noqa: F401
from test_p2_reasoning import make_plan
from uiux import api

CHECKOUT = "src/components/Checkout.tsx"


def clean_edits(plan):
    return [{"chunk_id": c["id"], "target_file": CHECKOUT, "target_component": "Checkout", "operation": "modify",
             "reason": "test", "new_content": "<div className='p-4'/>"} for c in plan["execution_chunks"]]


def session(viewports):
    return {"after_evidence": {"captures": [{"viewport": v, "route": "/", "status": "CAPTURED"} for v in viewports]},
            "change_manifest": {"changed_tokens": []}}


class PipelineToolTests(unittest.TestCase):
    def test_tools_are_registered_and_dispatchable(self) -> None:
        ids = {t["id"] for t in api.list_tools()}
        self.assertLessEqual({"check_execution_gate", "guard_edits", "verify_implementation"}, ids)

    def test_gate_via_call_tool(self) -> None:
        self.assertEqual(api.call_tool("check_execution_gate", {"plan": make_plan()})["status"], "PASS")
        self.assertEqual(api.call_tool("check_execution_gate", {"plan": make_plan(repo_profile={})})["status"], "BLOCKED")

    def test_full_chain_without_target_evidence_is_partial(self) -> None:
        plan = make_plan()
        report = api.call_tool("guard_edits", {"plan": plan, "edits": clean_edits(plan)})
        self.assertTrue(report["ready_for_p4"])
        result = api.call_tool("verify_implementation", {
            "implementation_report": report, "plan": plan, "session": session(plan["verification"]["viewports"])})
        self.assertEqual(result["verification_status"], "PARTIAL")
        self.assertEqual(result["trust_level"], "UNVERIFIED")
        self.assertEqual(result["accessibility"]["status"], "NOT_EVALUATED")

    def test_missing_viewport_evidence_is_partial(self) -> None:
        plan = make_plan()
        report = api.guard_edits(plan, clean_edits(plan))
        result = api.verify_implementation(report, session(plan["verification"]["viewports"][:1]), plan=plan)
        self.assertEqual(result["verification_status"], "PARTIAL")
        self.assertTrue(result["limitations"])

    def test_deviated_execution_blocks_verification(self) -> None:
        plan = make_plan()
        bad = clean_edits(plan)[:1] + [{"chunk_id": "chunk_0", "target_file": "src/App.tsx", "target_component": "App",
                                        "operation": "modify", "reason": "t", "new_content": "<x/>"}]
        report = api.guard_edits(plan, bad)
        self.assertEqual(report["status"], "DEVIATED")
        result = api.verify_implementation(report, session(plan["verification"]["viewports"]), plan=plan)
        self.assertEqual(result["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
