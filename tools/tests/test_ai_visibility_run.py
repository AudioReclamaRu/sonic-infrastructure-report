import csv
import hashlib
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


    def _verified_attestation(self):
        artifacts = {}
        for name, content in {
            "geo-a.txt": "geo vendor A RU",
            "geo-b.txt": "geo vendor B RU",
            "asn.txt": "local ISP",
            "session.txt": "consumer UI capture",
        }.items():
            path = self.root / name
            path.write_text(content, encoding="utf-8")
            artifacts[name] = {
                "evidence_file": name,
                "evidence_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        return {
            "schema": "studio/ai-visibility-region-attestation/1",
            "attestation_id": "ru-attestation-001",
            "observed_at_utc": "2026-11-17T12:00:00Z",
            "country_code": "RU", "interface_locale": "ru-RU",
            "network": {
                "connection_type": "residential_isp", "vpn_detected": False,
                "proxy_detected": False, "remote_desktop_detected": False,
                "ip_fingerprint_hmac_sha256": "a" * 64, "provider_name": "Local ISP",
            },
            "geolocation_sources": [
                {"provider": "Geo A", "independence_group": "A", "country_code": "RU",
                 "captured_at_utc": "2026-11-17T12:01:00Z", **artifacts["geo-a.txt"]},
                {"provider": "Geo B", "independence_group": "B", "country_code": "RU",
                 "captured_at_utc": "2026-11-17T12:02:00Z", **artifacts["geo-b.txt"]},
            ],
            "network_owner_evidence": {
                "provider": "ASN DB", "organization": "Local ISP",
                "network_class": "residential_isp", **artifacts["asn.txt"],
            },
            "session_capture": {
                "platform": "ChatGPT", "product": "Consumer UI", "interface_locale": "ru-RU",
                "captured_at_utc": "2026-11-17T12:03:00Z", **artifacts["session.txt"],
            },
            "operator_declaration": {
                "operator": "operator-a", "direct_connection": True, "no_vpn": True,
                "no_proxy": True, "no_remote_desktop": True,
            },
            "review": {
                "status": "APPROVED", "reviewer": "reviewer-b",
                "reviewed_at_utc": "2026-11-17T13:00:00Z", "rationale": "Reviewed independently.",
            },
        }

    def test_verified_region_requires_and_freezes_reviewed_attestation(self):
        attestation_path = self.root / "region-attestation.json"
        attestation_path.write_text(json.dumps(self._verified_attestation()), encoding="utf-8")
        rows = build_rows(load_module(self.module), region_status="VERIFIED")
        write_queue(rows, self.queue)
        output = self.root / "verified-passport.json"
        args = Namespace(
            output=output, run_id="run-verified-001", module=[str(self.module)],
            queue=[str(self.queue)], region_status="VERIFIED",
            region_attestation=attestation_path, notes="", operator_label="tester",
        )
        write_json(output, create_plan(args))
        errors, payload = validate_plan(output)
        self.assertEqual(errors, [])
        self.assertEqual(payload["scope"]["region_status"], "VERIFIED")
        self.assertIsNotNone(payload["scope"]["region_attestation"])

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

    def _verified_capture(self):
        attestation_path = self.root / "capture-region-attestation.json"
        attestation = self._verified_attestation()
        attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
        queue_path = self.root / "capture-queue.csv"
        write_queue(build_rows(load_module(self.module), region_status="VERIFIED"), queue_path)
        passport = self.root / "capture-passport.json"
        write_json(passport, create_plan(Namespace(
            output=passport, run_id="capture-run-001", module=[str(self.module)],
            queue=[str(queue_path)], region_status="VERIFIED",
            region_attestation=attestation_path, notes="", operator_label="tester",
        )))
        attestation_sha = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
        evidence_dir = self.root / "capture-evidence"
        evidence_dir.mkdir()
        record = {
            "schema": "studio/ai-visibility-observation/1",
            "observation_id": "obs-001", "run_id": "capture-run-001",
            "observed_at_utc": "2026-11-17T14:00:00Z",
            "market": {
                "country_code": "RU", "interface_locale": "ru-RU",
                "prompt_language": "ru", "answer_language": "ru",
                "region": "Moscow", "region_evidence": "Consumer UI capture in reviewed session",
                "region_attestation_id": "ru-attestation-001",
                "region_attestation_sha256": attestation_sha,
            },
            "platform": {
                "id": "chatgpt", "product": "ChatGPT", "surface": "consumer UI",
                "measurement_mode": "consumer_ui",
            },
            "query": {"query_id": "Q1", "intent": "generic", "exact_prompt": "Example prompt"},
            "answer_status": "OK", "raw_answer": "A complete captured answer.",
            "answer_excerpt": "A complete captured answer.", "named_providers": [],
            "generic_discovery_hit": False, "critical_error": False,
            "scores": {
                "brand_identity": 1, "official_route": 1, "service_or_answer": 1,
                "commercial_accuracy": 1, "expertise_retrieval": 1, "source_quality": 1,
                "citation_quality": 1, "git_knowledge": 1,
            },
            "evidence": {"sources": [], "repository_files": [], "capture_artifact": None},
            "limitations": [], "operator_notes": None,
        }
        record_path = evidence_dir / "obs-001.json"
        record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        csv_path = self.root / "capture-observations.csv"
        row = {
            "run_id": "capture-run-001", "country_code": "RU",
            "interface_locale": "ru-RU", "prompt_language": "ru", "answer_language": "ru",
            "platform": "chatgpt", "platform_surface": "consumer UI",
            "measurement_mode": "consumer_ui", "query_id": "Q1", "intent": "generic",
            "query": "Example prompt", "answer_status": "OK", "observation_id": "obs-001",
        }
        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(row))
            writer.writeheader()
            writer.writerow(row)
        return passport, csv_path, evidence_dir, record_path

    def test_result_passport_links_only_valid_run_scoped_evidence(self):
        passport, csv_path, evidence_dir, _ = self._verified_capture()
        result_path = self.root / "result.json"
        args = Namespace(
            passport=passport, run_id="capture-run-001",
            observations_csv=csv_path, evidence_dir=evidence_dir, output=result_path,
        )
        write_json(result_path, create_result(args))
        self.assertEqual(validate_result(result_path, passport), [])

    def test_finalization_rejects_wrong_observation_run_id(self):
        passport, csv_path, evidence_dir, record_path = self._verified_capture()
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["run_id"] = "different-run"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "run_id"):
            create_result(Namespace(
                passport=passport, run_id="capture-run-001",
                observations_csv=csv_path, evidence_dir=evidence_dir,
                output=self.root / "invalid-result.json",
            ))

    def test_finalization_rejects_wrong_region_attestation(self):
        passport, csv_path, evidence_dir, record_path = self._verified_capture()
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["market"]["region_attestation_id"] = "other-attestation"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "region_attestation_id"):
            create_result(Namespace(
                passport=passport, run_id="capture-run-001",
                observations_csv=csv_path, evidence_dir=evidence_dir,
                output=self.root / "invalid-result.json",
            ))

    def test_tampered_observation_artifact_invalidates_result(self):
        passport, csv_path, evidence_dir, _ = self._verified_capture()
        result_path = self.root / "result.json"
        args = Namespace(
            passport=passport, run_id="capture-run-001",
            observations_csv=csv_path, evidence_dir=evidence_dir, output=result_path,
        )
        write_json(result_path, create_result(args))
        csv_path.write_text(csv_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
        errors = validate_result(result_path, passport)
        self.assertTrue(any("SHA-256 mismatch" in error for error in errors))

    def test_result_must_reference_exact_plan_hash(self):
        passport, csv_path, evidence_dir, _ = self._verified_capture()
        result_path = self.root / "result.json"
        args = Namespace(
            passport=passport, run_id="capture-run-001",
            observations_csv=csv_path, evidence_dir=evidence_dir, output=result_path,
        )
        payload = create_result(args)
        payload["plan_passport_sha256"] = "0" * 64
        from tools.ai_visibility_run import seal
        write_json(result_path, seal(payload, "result_sha256"))
        errors = validate_result(result_path, passport)
        self.assertTrue(any("exact plan passport" in error for error in errors))

    def test_finalization_requires_both_csv_and_primary_records(self):
        with self.assertRaisesRegex(ValueError, "requires both"):
            create_result(Namespace(
                passport=self.passport, run_id="run-2026-11-17-001",
                observations_csv=None, evidence_dir=None, output=self.root / "none.json",
            ))


if __name__ == "__main__":
    unittest.main()
