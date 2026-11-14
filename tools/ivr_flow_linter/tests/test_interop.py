from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

LINTER_DIR = Path(__file__).resolve().parents[1]
if str(LINTER_DIR) not in sys.path:
    sys.path.insert(0, str(LINTER_DIR))

from interop.acfb_to_flow import convert_graph
from interop.flow_to_ivr_tester_plan import build_plan
from ivr_flow_lint import lint_flow


FIXTURE = LINTER_DIR / "examples" / "asterisk-call-flow-builder.graph.synthetic.json"


class InteropTests(unittest.TestCase):
    def acfb_graph(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_acfb_fixture_converts_to_valid_canonical_flow(self):
        flow, warnings = convert_graph(self.acfb_graph())
        result = lint_flow(flow)
        self.assertTrue(result.ok, [finding.message for finding in result.errors])
        self.assertEqual([], warnings)
        self.assertEqual(["__interop_start_prompt_start-1"], flow["entrypoints"])
        menu = next(node for node in flow["nodes"] if node["id"] == "welcome-1")
        self.assertEqual("end-1", menu["transitions"]["timeout"])
        self.assertEqual("end-1", menu["transitions"]["invalid_input"])
        self.assertEqual("support-1", menu["transitions"]["2"])

    def test_acfb_rejects_unknown_node_kind_instead_of_dropping_it(self):
        graph = self.acfb_graph()
        graph["nodes"][1]["data"]["kind"] = "vendor-specific"
        with self.assertRaisesRegex(ValueError, "unsupported ACFB node kind"):
            convert_graph(graph)

    def test_acfb_rejects_missing_edge_target(self):
        graph = self.acfb_graph()
        graph["edges"][0]["target"] = "missing-node"
        with self.assertRaisesRegex(ValueError, "references missing target"):
            convert_graph(graph)

    def test_acfb_rejects_unsupported_graph_version(self):
        graph = self.acfb_graph()
        graph["version"] = 2
        with self.assertRaisesRegex(ValueError, "unsupported ACFB graph version"):
            convert_graph(graph)

    def test_acfb_rejects_duplicate_outgoing_handle(self):
        graph = self.acfb_graph()
        graph["edges"].append({
            "id": "duplicate",
            "source": "welcome-1",
            "sourceHandle": "option-1",
            "target": "end-1",
        })
        with self.assertRaisesRegex(ValueError, "duplicate outgoing handle"):
            convert_graph(graph)

    def test_acfb_warns_when_extension_outcomes_would_be_collapsed_by_exporter(self):
        graph = self.acfb_graph()
        graph["edges"].append({
            "id": "support-busy",
            "source": "support-1",
            "sourceHandle": "busy",
            "target": "end-1",
        })
        _, warnings = convert_graph(graph)
        self.assertTrue(any("ACFB_EXTENSION_EXPORT_FIRST_EDGE_ONLY" in warning for warning in warnings))

    def test_acfb_warns_when_queue_result_handles_would_be_collapsed(self):
        graph = self.acfb_graph()
        graph["edges"].append({
            "id": "queue-timeout",
            "source": "queue-1",
            "sourceHandle": "timeout",
            "target": "end-1",
        })
        _, warnings = convert_graph(graph)
        self.assertTrue(any("ACFB_QUEUE_EXPORT_COLLAPSES_RESULT_HANDLES" in warning for warning in warnings))

    def test_ivr_tester_plan_maps_dtmf_timeout_and_invalid_input(self):
        flow, _ = convert_graph(self.acfb_graph())
        plan = build_plan(flow)
        self.assertFalse(plan["runtime_ready"])
        self.assertEqual(5, len(plan["scenarios"]))
        self.assertEqual(2, len(plan["manual_routes"]))
        actions = [
            step["then"]
            for scenario in plan["scenarios"]
            for step in scenario["steps"]
        ]
        self.assertIn({"method": "press", "digits": "1"}, actions)
        self.assertIn({"method": "doNothing"}, actions)
        self.assertIn({"method": "press", "digits": "0"}, actions)

    def test_ivr_tester_plan_never_guesses_prompt_transcripts(self):
        flow, _ = convert_graph(self.acfb_graph())
        plan = build_plan(flow)
        for scenario in plan["scenarios"]:
            for step in scenario["steps"]:
                self.assertIsNone(step["expected_prompt_transcript"])
                self.assertTrue(step["requires_actual_prompt_transcript"])

    def test_ivr_tester_plan_marks_cycles_for_manual_review(self):
        flow = {
            "schema_version": "1.0",
            "flow_id": "cycle-test",
            "entrypoints": ["menu"],
            "policy": {
                "require_operator_escape": False,
                "require_timeout_fallback": True,
                "require_invalid_input_fallback": True,
            },
            "nodes": [
                {"id": "menu", "type": "menu", "transitions": {
                    "1": "menu", "timeout": "end", "invalid_input": "end"
                }},
                {"id": "end", "type": "terminal", "terminal_kind": "hangup", "transitions": {}},
            ],
        }
        plan = build_plan(flow)
        self.assertTrue(plan["blocked_cycles"])
        self.assertEqual("manual_review_required", plan["blocked_cycles"][0]["status"])

    def test_plan_rejects_invalid_flow(self):
        flow, _ = convert_graph(self.acfb_graph())
        broken = copy.deepcopy(flow)
        menu = next(node for node in broken["nodes"] if node["id"] == "welcome-1")
        menu["transitions"].pop("timeout")
        with self.assertRaisesRegex(ValueError, "flow has lint errors"):
            build_plan(broken)


if __name__ == "__main__":
    unittest.main(verbosity=2)
