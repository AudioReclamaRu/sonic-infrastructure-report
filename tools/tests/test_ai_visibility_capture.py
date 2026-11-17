import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ai_visibility_capture import build_packet


class CapturePacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.passport = self.root / "passport.json"
        self.passport.write_text("{}", encoding="utf-8")
        self.queue = self.root / "queue.csv"
        row = {
            "queue_id": "Q1-chatgpt", "module_id": "module-1", "module_version": "1.0",
            "query_id": "Q1", "query": "Example prompt", "intent": "generic",
            "country_code": "RU", "interface_locale": "ru-RU",
            "prompt_language": "ru", "answer_language": "ru",
            "platform": "chatgpt", "platform_surface": "consumer UI",
            "measurement_mode": "consumer_ui", "execution_status": "NOT_TESTED",
            "region_verification": "VERIFIED",
        }
        with self.queue.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(row))
            writer.writeheader()
            writer.writerow(row)
        self.attestation = self.root / "region.json"
        self.attestation.write_text(json.dumps({
            "attestation_id": "attestation-001",
            "session_capture": {"captured_at_utc": "2026-11-17T15:00:00Z"},
        }), encoding="utf-8")
        self.plan = {
            "run_id": "run-001",
            "passport_sha256": "a" * 64,
            "scope": {
                "region_status": "VERIFIED",
                "region_attestation": {
                    "path": "region.json",
                    "sha256": hashlib.sha256(self.attestation.read_bytes()).hexdigest(),
                },
            },
            "matrix_totals": {"planned_cells": 1},
            "artifacts": {
                "execution_queues": [{
                    "path": "queue.csv",
                    "sha256": hashlib.sha256(self.queue.read_bytes()).hexdigest(),
                }],
            },
        }

    def test_creates_blank_templates_bound_to_verified_plan(self):
        output = self.root / "packet"
        with patch("tools.ai_visibility_capture.validate_plan", return_value=([], self.plan)):
            manifest = build_packet(self.passport, output)
        self.assertEqual(manifest["packet_status"], "DRAFT_TEMPLATES_ONLY")
        self.assertEqual(manifest["planned_cells"], 1)
        self.assertTrue((output / "capture.csv").is_file())
        self.assertTrue((output / "README_CAPTURE.md").is_file())
        template_path = output / manifest["evidence_templates"][0]
        template = json.loads(template_path.read_text(encoding="utf-8"))
        self.assertEqual(template["answer_status"], "NOT_TESTED")
        self.assertEqual(template["observed_at_utc"], "")
        self.assertEqual(template["market"]["region_attestation_id"], "attestation-001")
        self.assertEqual(template["market"]["region_attestation_sha256"], self.plan["scope"]["region_attestation"]["sha256"])

    def test_refuses_unverified_plan(self):
        output = self.root / "packet"
        plan = dict(self.plan)
        plan["scope"] = {"region_status": "UNVERIFIED", "region_attestation": None}
        with patch("tools.ai_visibility_capture.validate_plan", return_value=([], plan)):
            with self.assertRaisesRegex(ValueError, "requires a VERIFIED"):
                build_packet(self.passport, output)
        self.assertFalse(output.exists())

    def test_refuses_to_overwrite_existing_packet_directory(self):
        output = self.root / "packet"
        output.mkdir()
        with patch("tools.ai_visibility_capture.validate_plan", return_value=([], self.plan)):
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                build_packet(self.passport, output)


if __name__ == "__main__":
    unittest.main()
