from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "check_experiment_records.py"
spec = importlib.util.spec_from_file_location("check_experiment_records", TOOL)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ExperimentRecordTests(unittest.TestCase):
    def valid_record(self):
        return {
            "schema_version": "1.0",
            "record_kind": "experiment",
            "experiment_id": "EXP-SYNTHETIC-001",
            "status": "PLANNED",
            "experiment_type": "synthetic unit-test fixture",
            "protocol_version": "1.0",
            "created_at": "2026-11-15T20:00:00Z",
            "owner": "SYNTHETIC-TEST-OWNER",
            "question": "Does the validation gate reject an incomplete review?",
            "hypothesis": "A complete six-lens record passes.",
            "null_hypothesis": "A missing or incomplete lens is rejected.",
            "falsifier": "A deliberately incomplete lens passes validation.",
            "scope": "Validator unit tests only; no real-world experiment.",
            "variables": [{
                "name": "lens_status",
                "role": "independent",
                "operational_definition": "The declared status for one review lens.",
                "unit": "categorical",
                "measurement_method": "Read the JSON value."
            }],
            "controls": ["All test records are generated in memory."],
            "six_lenses": {
                lens: {
                    "status": "APPLICABLE",
                    "risk": "Synthetic low-risk validator test.",
                    "assessment": "A test fixture checks schema gate behaviour.",
                    "check": "Assert expected validation result.",
                    "rationale": "",
                    "evidence": ["SYNTHETIC-UNIT-TEST"]
                    ,"hold_reason": ""
                }
                for lens in module.LENSES
            },
            "data_provenance": {
                "sources": ["SYNTHETIC-UNIT-TEST"],
                "collection_method": "Constructed in test code; no external data.",
                "data_classification": "public",
                "hashes": []
            },
            "analysis_plan": "Run deterministic unit assertions.",
            "external_release": False,
            "synthetic_fixture": True
        }

    def test_complete_planned_record_passes(self):
        errors = module.validate_record(self.valid_record())
        self.assertEqual([], errors)

    def test_every_lens_is_required(self):
        record = self.valid_record()
        record["six_lenses"].pop("chronobiology")
        errors = module.validate_record(record)
        self.assertTrue(any("missing six-lens review: chronobiology" in x for x in errors))

    def test_unknown_lens_is_rejected(self):
        record = self.valid_record()
        record["six_lenses"]["intuition"] = record["six_lenses"]["semiotics"]
        errors = module.validate_record(record)
        self.assertTrue(any("unknown six-lens key: intuition" in x for x in errors))

    def test_not_applicable_requires_rationale(self):
        record = self.valid_record()
        record["six_lenses"]["chronobiology"]["status"] = "NOT_APPLICABLE"
        record["six_lenses"]["chronobiology"]["check"] = ""
        errors = module.validate_record(record)
        self.assertTrue(any("NOT_APPLICABLE requires a rationale" in x for x in errors))

    def test_not_assessed_requires_reason_but_is_allowed_while_planned(self):
        record = self.valid_record()
        lens = record["six_lenses"]["ethology_behavior"]
        lens.update({
            "status": "NOT_ASSESSED",
            "check": "",
            "rationale": "No human, animal or agent behaviour is observed in this planned unit test."
        })
        self.assertEqual([], module.validate_record(record))

    def test_completed_record_cannot_leave_lens_not_assessed(self):
        record = self.valid_record()
        record["status"] = "COMPLETED"
        record["started_at"] = "2026-11-15T20:10:00Z"
        record["completed_at"] = "2026-11-15T20:11:00Z"
        record["results"] = {
            "run_id": "SYNTHETIC-RUN-001",
            "observations": ["No external data used."],
            "measurements": ["All assertions evaluated."],
            "limitations": ["Unit test only; no real-world inference."],
            "verdict": "SUPPORTED"
        }
        lens = record["six_lenses"]["chronobiology"]
        lens.update({
            "status": "NOT_ASSESSED",
            "check": "",
            "rationale": "Not included in the synthetic validator test."
        })
        errors = module.validate_record(record)
        self.assertTrue(any("cannot leave a lens NOT_ASSESSED" in x for x in errors))

    def test_completed_record_passes_when_all_lenses_reviewed(self):
        record = self.valid_record()
        record["status"] = "COMPLETED"
        record["started_at"] = "2026-11-15T20:10:00Z"
        record["completed_at"] = "2026-11-15T20:11:00Z"
        record["results"] = {
            "run_id": "SYNTHETIC-RUN-002",
            "observations": ["Validator accepted a complete fixture."],
            "measurements": ["No external data used."],
            "limitations": ["Unit test only; no real-world inference."],
            "verdict": "SUPPORTED"
        }
        for lens in module.LENSES:
            record["six_lenses"][lens]["evidence"] = ["SYNTHETIC-UNIT-TEST-RESULT"]
        self.assertEqual([], module.validate_record(record))

    def test_lens_hold_requires_overall_hold(self):
        record = self.valid_record()
        lens = record["six_lenses"]["cryptology"]
        lens.update({
            "status": "HOLD",
            "check": "",
            "rationale": "",
            "hold_reason": "Synthetic hold condition."
        })
        errors = module.validate_record(record)
        self.assertTrue(any("requires overall status HOLD" in x for x in errors))

    def test_hold_record_requires_reason(self):
        record = self.valid_record()
        record["status"] = "HOLD"
        errors = module.validate_record(record)
        self.assertTrue(any("overall HOLD requires hold_reason" in x for x in errors))

    def test_external_release_requires_approval(self):
        record = self.valid_record()
        record["status"] = "COMPLETED"
        record["started_at"] = "2026-11-15T20:10:00Z"
        record["completed_at"] = "2026-11-15T20:11:00Z"
        record["results"] = {
            "run_id": "SYNTHETIC-RUN-003",
            "observations": [],
            "measurements": [],
            "limitations": ["Synthetic only."],
            "verdict": "INCONCLUSIVE"
        }
        record["external_release"] = True
        errors = module.validate_record(record)
        self.assertTrue(any("requires release_approval" in x for x in errors))

    def test_external_release_passes_only_with_approval_and_real_record(self):
        record = self.valid_record()
        record["synthetic_fixture"] = False
        record["status"] = "COMPLETED"
        record["started_at"] = "2026-11-15T20:10:00Z"
        record["completed_at"] = "2026-11-15T20:11:00Z"
        record["results"] = {
            "run_id": "SYNTHETIC-RUN-004",
            "observations": ["Approved synthetic validator fixture; not a studio study."],
            "measurements": ["Six lens checks recorded."],
            "limitations": ["Validator test only."],
            "verdict": "SUPPORTED"
        }
        record["external_release"] = True
        record["release_approval"] = {
            "approved_by": "SYNTHETIC-TEST-APPROVER",
            "approved_at": "2026-11-15T20:12:00Z",
            "approval_ref": "SYNTHETIC-TEST-APPROVAL"
        }
        self.assertEqual([], module.validate_record(record))

    def test_completed_applicable_lens_needs_evidence(self):
        record = self.valid_record()
        record["status"] = "COMPLETED"
        record["started_at"] = "2026-11-15T20:10:00Z"
        record["completed_at"] = "2026-11-15T20:11:00Z"
        record["results"] = {
            "run_id": "SYNTHETIC-RUN-005",
            "observations": [],
            "measurements": [],
            "limitations": ["Validator only."],
            "verdict": "INCONCLUSIVE"
        }
        record["six_lenses"]["semiotics"]["evidence"] = []
        errors = module.validate_record(record)
        self.assertTrue(any("requires evidence for APPLICABLE lens" in x for x in errors))

    def test_synthetic_fixture_cannot_be_externally_released(self):
        record = self.valid_record()
        record["external_release"] = True
        record["release_approval"] = {
            "approved_by": "SYNTHETIC-APPROVER",
            "approved_at": "2026-11-15T20:00:00Z",
            "approval_ref": "SYNTHETIC-APPROVAL"
        }
        errors = module.validate_record(record)
        self.assertTrue(any("synthetic fixture cannot be externally released" in x for x in errors))

    def test_hash_format_matches_declared_algorithm(self):
        record = self.valid_record()
        record["data_provenance"]["hashes"] = [{
            "algorithm": "SHA-256",
            "digest": "abc123",
            "object_ref": "SYNTHETIC-OBJECT"
        }]
        errors = module.validate_record(record)
        self.assertTrue(any("digest has invalid length/format" in x for x in errors))

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.json"
            path.write_text('{"status":"PLANNED","status":"COMPLETED"}', encoding="utf-8")
            with self.assertRaises(module.DuplicateKeyError):
                module.load_json(path)

    def test_schema_declares_six_lens_contract(self):
        schema_path = module.SCHEMA
        schema = module.load_json(schema_path)
        six_required = schema["properties"]["six_lenses"]["required"]
        self.assertEqual(set(module.LENSES), set(six_required))
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
