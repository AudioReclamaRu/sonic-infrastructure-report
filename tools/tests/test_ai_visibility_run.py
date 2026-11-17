import csv
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from tools.ai_visibility_run import (
    create_plan, create_result, validate_plan, validate_result, write_json,
)
from tools.ai_visibility_queue import build_rows, load_module, write_queue


class RunPassportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.module = self.root / "queries.json"
        self.module.write_text(json.dumps({
            "schema": "studio/ai-visibility-query-module/1",
            "version": "1.0",
            "queries": [{"id": "Q1", "query": "Example prompt", "intent": "generic"}],
            "platform_execution_order": [{
                "id": "chatgpt", "surface": "consumer UI",
                "measurement_mode": "consumer_ui", "priority": "1",
            }],
            "market": {
                "country_code": "RU", "interface_locale": "ru-RU",
                "prompt_language": "ru", "answer_language": "ru",
            },
        }), encoding="utf-8")
        self.queue = self.root / "queue.csv"
        write_queue(build_rows(load_module(self.module)), self.queue)
        self.passport = self.root / "passport.json"
        args = Namespace(
            output=self.passport, run_id="run-2026-11-17-001",
            module=[str(self.module)], queue=[str(self.queue)],
            region_status="UNVERIFIED", region_attestation=None, notes="test", operator_label="tester",
        )
        write_json(self.passport, create_plan(args))

    def test_plan_passport_seals_and_verifies_inputs(self):
        errors, payload = validate_plan(self.passport)
        self.assertEqual(errors, [])
        self.assertEqual(payload["matrix_totals"]["planned_cells"], 1)
        self.assertEqual(payload["scope"]["region_status"], "UNVERIFIED")

    def test_modified_frozen_input_is_detected(self):
        self.queue.write_text(self.queue.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        errors, _ = validate_plan(self.passport)
        self.assertTrue(any("SHA-256 mismatch" in error for error in errors))

    def test_modified_passport_payload_is_detected(self):
        payload = json.loads(self.passport.read_text(encoding="utf-8"))
        payload["scope"]["operator_label"] = "altered"
        self.passport.write_text(json.dumps(payload), encoding="utf-8")
        errors, _ = validate_plan(self.passport)
        self.assertTrue(any("passport_sha256 mismatch" in error for error in errors))

    def test_result_passport_links_plan_and_observation_artifacts(self):
        csv_path = self.root / "observations.csv"
        csv_path.write_text("run_id,observation_id\nrun-2026-11-17-001,obs-1\n", encoding="utf-8")
        evidence_dir = self.root / "evidence"
        evidence_dir.mkdir()
        (evidence_dir / "obs-1.json").write_text('{"observation_id":"obs-1"}', encoding="utf-8")
        result_path = self.root / "result.json"
        args = Namespace(
            passport=self.passport, run_id="run-2026-11-17-001",
            observations_csv=csv_path, evidence_dir=evidence_dir, output=result_path,
        )
        write_json(result_path, create_result(args))
        self.assertEqual(validate_result(result_path, self.passport), [])

    def test_tampered_observation_artifact_invalidates_result(self):
        csv_path = self.root / "observations.csv"
        csv_path.write_text("run_id,observation_id\nrun-2026-11-17-001,obs-1\n", encoding="utf-8")
        result_path = self.root / "result.json"
        args = Namespace(
            passport=self.passport, run_id="run-2026-11-17-001",
            observations_csv=csv_path, evidence_dir=None, output=result_path,
        )
        write_json(result_path, create_result(args))
        csv_path.write_text(csv_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
        errors = validate_result(result_path, self.passport)
        self.assertTrue(any("SHA-256 mismatch" in error for error in errors))

    def test_result_must_reference_exact_plan_hash(self):
        csv_path = self.root / "observations.csv"
        csv_path.write_text("run_id,observation_id\nrun-2026-11-17-001,obs-1\n", encoding="utf-8")
        result_path = self.root / "result.json"
        args = Namespace(
            passport=self.passport, run_id="run-2026-11-17-001",
            observations_csv=csv_path, evidence_dir=None, output=result_path,
        )
        payload = create_result(args)
        payload["plan_passport_sha256"] = "0" * 64
        from tools.ai_visibility_run import seal
        write_json(result_path, seal(payload, "result_sha256"))
        errors = validate_result(result_path, self.passport)
        self.assertTrue(any("exact plan passport" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
