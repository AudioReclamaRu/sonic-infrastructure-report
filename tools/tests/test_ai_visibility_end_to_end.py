import csv
import hashlib
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from tools.ai_visibility_capture import build_packet
from tools.ai_visibility_queue import build_rows, load_module, write_queue
from tools.ai_visibility_region import validate_attestation
from tools.ai_visibility_run import create_plan, create_result, validate_plan, validate_result, write_json
from tools.ai_visibility_report import build_report, render_markdown


class FullVisibilityPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.module_path = self.root / "queries.json"
        self.module_path.write_text(json.dumps({
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
        self.queue_path = self.root / "queue.csv"
        write_queue(build_rows(load_module(self.module_path), region_status="VERIFIED"), self.queue_path)
        self.attestation_path = self.root / "region-attestation.json"
        self.attestation = self._make_attestation()
        self.attestation_path.write_text(json.dumps(self.attestation, ensure_ascii=False), encoding="utf-8")
        errors, status = validate_attestation(self.attestation, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(status, "VERIFIED")
        self.passport_path = self.root / "passport.json"
        write_json(self.passport_path, create_plan(Namespace(
            output=self.passport_path, run_id="integration-run-001",
            module=[str(self.module_path)], queue=[str(self.queue_path)],
            region_status="VERIFIED", region_attestation=self.attestation_path,
            notes="Synthetic integration fixture only", operator_label="test-suite",
        )))

    def _make_attestation(self):
        artifacts = {}
        for name, body in {
            "geo-a.txt": "synthetic geo provider A fixture",
            "geo-b.txt": "synthetic geo provider B fixture",
            "asn.txt": "synthetic local ISP registry fixture",
            "session.txt": "synthetic consumer UI screenshot fixture",
        }.items():
            path = self.root / name
            path.write_text(body, encoding="utf-8")
            artifacts[name] = {
                "evidence_file": name,
                "evidence_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        return {
            "schema": "studio/ai-visibility-region-attestation/1",
            "attestation_id": "synthetic-test-attestation",
            "observed_at_utc": "2026-11-17T12:00:00Z",
            "country_code": "RU", "interface_locale": "ru-RU",
            "network": {
                "connection_type": "residential_isp", "vpn_detected": False,
                "proxy_detected": False, "remote_desktop_detected": False,
                "ip_fingerprint_hmac_sha256": "a" * 64,
                "provider_name": "Synthetic ISP fixture",
            },
            "geolocation_sources": [
                {"provider": "Geo A", "independence_group": "A", "country_code": "RU",
                 "captured_at_utc": "2026-11-17T12:01:00Z", **artifacts["geo-a.txt"]},
                {"provider": "Geo B", "independence_group": "B", "country_code": "RU",
                 "captured_at_utc": "2026-11-17T12:02:00Z", **artifacts["geo-b.txt"]},
            ],
            "network_owner_evidence": {
                "provider": "Synthetic ASN registry", "organization": "Synthetic ISP fixture",
                "network_class": "residential_isp", **artifacts["asn.txt"],
            },
            "session_capture": {
                "platform": "ChatGPT", "product": "Consumer UI", "interface_locale": "ru-RU",
                "captured_at_utc": "2026-11-17T12:03:00Z", **artifacts["session.txt"],
            },
            "operator_declaration": {
                "operator": "synthetic-test-operator", "direct_connection": True,
                "no_vpn": True, "no_proxy": True, "no_remote_desktop": True,
            },
            "review": {
                "status": "APPROVED", "reviewer": "synthetic-independent-reviewer",
                "reviewed_at_utc": "2026-11-17T12:04:00Z",
                "rationale": "Synthetic fixture for automated integration testing only.",
            },
        }

    def test_prepare_capture_finalize_validate_and_report(self):
        packet_dir = self.root / "capture-packet"
        packet = build_packet(self.passport_path, packet_dir)
        self.assertEqual(packet["packet_status"], "DRAFT_TEMPLATES_ONLY")
        self.assertEqual(packet["planned_cells"], 1)

        template_path = packet_dir / packet["evidence_templates"][0]
        record = json.loads(template_path.read_text(encoding="utf-8"))
        self.assertEqual(record["answer_status"], "NOT_TESTED")
        record["observed_at_utc"] = "2026-11-17T12:10:00Z"
        record["market"]["region"] = "Moscow"
        record["market"]["region_evidence"] = "Synthetic fixture: session locale and test geolocation pack"
        record["platform"]["product"] = "ChatGPT consumer product"
        record["answer_status"] = "OK"
        record["raw_answer"] = "Synthetic test answer; not a real AI observation."
        record["answer_excerpt"] = "Synthetic test answer."
        record["generic_discovery_hit"] = False
        record["critical_error"] = False
        record["scores"] = {key: 1 for key in record["scores"]}
        record["operator_notes"] = "Synthetic fixture only; not collected from a live service."
        template_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        capture_csv = packet_dir / "capture.csv"
        with capture_csv.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = list(reader.fieldnames)
            rows = list(reader)
        row = rows[0]
        row.update({
            "date_utc": "2026-11-17",
            "date_time_utc": "2026-11-17T12:10:00Z",
            "region": "Moscow",
            "product_or_model": "ChatGPT consumer product",
            "answer_status": "OK",
            "completeness_status": "complete",
            "brand_identity_score": "1",
            "official_route_score": "1",
            "service_or_answer_score": "1",
            "commercial_accuracy_score": "1",
            "expertise_retrieval_score": "1",
            "source_quality_score": "1",
            "citation_quality_score": "1",
            "git_knowledge_score": "1",
            "generic_discovery_hit": "false",
            "critical_error": "false",
            "answer_excerpt": "Synthetic test answer.",
            "observation_id": record["observation_id"],
        })
        with capture_csv.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)

        result_path = self.root / "result.json"
        result = create_result(Namespace(
            passport=self.passport_path,
            run_id="integration-run-001",
            observations_csv=capture_csv,
            evidence_dir=packet_dir / "evidence",
            output=result_path,
        ))
        write_json(result_path, result)
        self.assertEqual(validate_result(result_path, self.passport_path), [])

        report = build_report(self.passport_path, result_path)
        self.assertEqual(report["run"]["run_id"], "integration-run-001")
        self.assertEqual(report["coverage"]["totals"]["coverage_pct"], 100.0)
        self.assertEqual(report["benchmark"]["groups"][0]["answered"], 1)
        self.assertIn("not zero visibility", render_markdown(report).lower())


if __name__ == "__main__":
    unittest.main()
