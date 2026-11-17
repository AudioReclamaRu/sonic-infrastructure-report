import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ai_visibility_report import build_report, render_markdown


class VisibilityFinalReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.passport = self.root / "passport.json"
        self.result = self.root / "result.json"
        self.queue = self.root / "queue.csv"
        self.observations = self.root / "observations.csv"
        self.record = self.root / "obs-001.json"

        queue_row = {
            "queue_id": "Q1-chatgpt", "module_id": "module-1", "module_version": "1.0",
            "query_id": "Q1", "query": "Example prompt", "intent": "generic",
            "country_code": "RU", "interface_locale": "ru-RU",
            "prompt_language": "ru", "answer_language": "ru",
            "platform": "chatgpt", "platform_surface": "consumer UI",
            "measurement_mode": "consumer_ui", "execution_status": "NOT_TESTED",
            "region_verification": "VERIFIED",
        }
        with self.queue.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(queue_row))
            writer.writeheader()
            writer.writerow(queue_row)

        observation_row = {
            "run_id": "run-001", "date_utc": "2026-11-17",
            "country_code": "RU", "interface_locale": "ru-RU",
            "prompt_language": "ru", "answer_language": "ru",
            "platform": "chatgpt", "product_or_model": "ChatGPT",
            "platform_surface": "consumer UI", "measurement_mode": "consumer_ui",
            "intent": "generic", "query_id": "Q1", "query": "Example prompt",
            "answer_status": "OK", "completeness_status": "complete",
            "observation_id": "obs-001", "generic_discovery_hit": "true",
            "critical_error": "false",
            "brand_identity_score": "1", "official_route_score": "2",
            "service_or_answer_score": "2", "commercial_accuracy_score": "1",
            "expertise_retrieval_score": "1", "source_quality_score": "2",
            "citation_quality_score": "1", "git_knowledge_score": "0",
        }
        with self.observations.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(observation_row))
            writer.writeheader()
            writer.writerow(observation_row)
        self.record.write_text('{"observation_id":"obs-001"}', encoding="utf-8")
        self.passport.write_text(json.dumps({
            "run_id": "run-001",
            "passport_sha256": "a" * 64,
            "scope": {"region_status": "VERIFIED"},
            "matrix_totals": {"planned_cells": 1},
            "artifacts": {
                "execution_queues": [{"path": "queue.csv", "sha256": "b" * 64}],
            },
        }), encoding="utf-8")
        self.result.write_text(json.dumps({
            "lifecycle": "FINALIZED",
            "result_sha256": "c" * 64,
            "observation_artifacts": {
                "benchmark_csv": {"path": "observations.csv"},
                "primary_json_records": [{"path": "obs-001.json"}],
            },
        }), encoding="utf-8")

    def test_builds_combined_coverage_and_answered_only_report(self):
        with patch("tools.ai_visibility_report.validate_result", return_value=[]):
            report = build_report(self.passport, self.result)
        self.assertEqual(report["run"]["run_id"], "run-001")
        self.assertEqual(report["coverage"]["totals"]["coverage_pct"], 100.0)
        self.assertEqual(report["benchmark"]["groups"][0]["answered"], 1)
        self.assertEqual(report["benchmark"]["groups"][0]["generic_discovery_rate"], 1.0)
        markdown = render_markdown(report)
        self.assertIn("Answered-only benchmark groups", markdown)
        self.assertIn("not zero visibility", markdown)

    def test_refuses_unvalidated_result_passport(self):
        with patch("tools.ai_visibility_report.validate_result", return_value=["result hash mismatch"]):
            with self.assertRaisesRegex(ValueError, "result hash mismatch"):
                build_report(self.passport, self.result)


if __name__ == "__main__":
    unittest.main()
