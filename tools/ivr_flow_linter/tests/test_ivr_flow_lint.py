from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "ivr_flow_lint.py"
spec = importlib.util.spec_from_file_location("ivr_flow_lint", TOOL)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class IvrFlowLintTests(unittest.TestCase):
    def valid_flow(self):
        return {
            "schema_version": "1.0",
            "flow_id": "synthetic-support",
            "entrypoints": ["welcome"],
            "policy": {
                "require_operator_escape": True,
                "require_timeout_fallback": True,
                "require_invalid_input_fallback": True,
            },
            "nodes": [
                {"id": "welcome", "type": "menu", "transitions": {
                    "1": "sales", "2": "support", "timeout": "operator", "invalid_input": "operator"
                }},
                {"id": "sales", "type": "message", "transitions": {"continue": "operator"}},
                {"id": "support", "type": "message", "transitions": {"continue": "operator"}},
                {"id": "operator", "type": "terminal", "terminal_kind": "operator", "transitions": {}},
            ],
        }

    def codes(self, data):
        return {f.code for f in module.lint_flow(data).findings}

    def test_valid_flow_passes(self):
        result = module.lint_flow(self.valid_flow())
        self.assertTrue(result.ok, module.render_text(result))
        self.assertEqual([], result.errors)

    def test_missing_transition_target_fails(self):
        data = self.valid_flow()
        data["nodes"][0]["transitions"]["1"] = "missing"
        self.assertIn("MISSING_TARGET", self.codes(data))

    def test_missing_menu_fallbacks_fail(self):
        data = self.valid_flow()
        data["nodes"][0]["transitions"].pop("timeout")
        data["nodes"][0]["transitions"].pop("invalid_input")
        codes = self.codes(data)
        self.assertIn("MISSING_TIMEOUT", codes)
        self.assertIn("MISSING_INVALID_INPUT", codes)

    def test_unreachable_node_warns(self):
        data = self.valid_flow()
        data["nodes"].append({"id": "orphan", "type": "terminal", "terminal_kind": "hangup", "transitions": {}})
        result = module.lint_flow(data)
        self.assertIn("UNREACHABLE_NODE", {f.code for f in result.warnings})
        self.assertTrue(result.ok)

    def test_closed_loop_without_terminal_fails(self):
        data = self.valid_flow()
        data["nodes"][0]["transitions"] = {"timeout": "welcome", "invalid_input": "welcome"}
        result = module.lint_flow(data)
        self.assertIn("NO_TERMINAL_PATH", {f.code for f in result.errors})

    def test_operator_escape_policy_fails_without_operator_path(self):
        data = self.valid_flow()
        data["nodes"] = [
            {"id": "welcome", "type": "menu", "transitions": {"1": "end", "timeout": "end", "invalid_input": "end"}},
            {"id": "end", "type": "terminal", "terminal_kind": "hangup", "transitions": {}},
        ]
        result = module.lint_flow(data)
        self.assertIn("NO_OPERATOR_ESCAPE", {f.code for f in result.errors})

    def test_duplicate_node_id_fails(self):
        data = self.valid_flow()
        data["nodes"].append(dict(data["nodes"][-1]))
        self.assertIn("DUPLICATE_NODE_ID", self.codes(data))

    def test_duplicate_json_key_is_rejected(self):
        raw = '{"schema_version":"1.0","schema_version":"1.0"}'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.json"
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(ValueError):
                module.load_flow(path)

    def test_missing_flow_id_fails(self):
        data = self.valid_flow()
        data.pop("flow_id")
        self.assertIn("FLOW_ID", {f.code for f in module.lint_flow(data).errors})

    def test_malformed_entrypoint_fails(self):
        data = self.valid_flow()
        data["entrypoints"] = ["welcome", 17]
        self.assertIn("ENTRYPOINT_VALUE", {f.code for f in module.lint_flow(data).errors})

    def test_hangup_terminal_is_allowed_when_operator_escape_policy_is_set(self):
        data = self.valid_flow()
        data["nodes"].append({"id": "end_call", "type": "terminal", "terminal_kind": "hangup", "transitions": {}})
        data["nodes"][0]["transitions"]["9"] = "end_call"
        result = module.lint_flow(data)
        self.assertNotIn("NO_OPERATOR_ESCAPE", {f.code for f in result.errors})

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "flow.json"
            path.write_text(json.dumps(self.valid_flow()), encoding="utf-8")
            ok = subprocess.run([sys.executable, str(TOOL), str(path), "--json"], capture_output=True, text=True)
            self.assertEqual(0, ok.returncode, ok.stderr)
            bad_data = self.valid_flow()
            bad_data["nodes"][0]["transitions"]["1"] = "not-found"
            path.write_text(json.dumps(bad_data), encoding="utf-8")
            bad = subprocess.run([sys.executable, str(TOOL), str(path)], capture_output=True, text=True)
            self.assertEqual(1, bad.returncode)
            self.assertIn("MISSING_TARGET", bad.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
