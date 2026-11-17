import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ai_visibility_prepare_run import prepare_run


class PrepareRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.module = self.root / "queries.json"
        self.module.write_text('{"schema":"test-module"}', encoding="utf-8")
        self.attestation = self.root / "region.json"
        self.attestation.write_text(json.dumps({"attestation_id": "attestation-001"}), encoding="utf-8")

    def test_builds_one_complete_run_package_atomically(self):
        output = self.root / "run-package"
        rows = [{"queue_id": "Q1"}]
        plan = {"run_id": "run-001", "passport_sha256": "a" * 64}
        with (
            patch("tools.ai_visibility_prepare_run.load_module", return_value={"schema": "test-module"}),
            patch("tools.ai_visibility_prepare_run.validate_attestation", return_value=([], "VERIFIED")),
            patch("tools.ai_visibility_prepare_run.build_rows", return_value=rows),
            patch("tools.ai_visibility_prepare_run.write_queue", side_effect=lambda _rows, path: path.write_text("queue fixture", encoding="utf-8")),
            patch("tools.ai_visibility_prepare_run.create_plan", return_value=plan),
            patch("tools.ai_visibility_prepare_run.validate_plan", return_value=([], plan)),
            patch("tools.ai_visibility_prepare_run.build_packet", return_value={"schema": "packet/1", "planned_cells": 1}),
        ):
            manifest = prepare_run(self.module, self.attestation, "run-001", output)
        self.assertEqual(manifest["package_status"], "PLANNED_CAPTURE_READY")
        self.assertTrue((output / "queue.csv").is_file())
        self.assertTrue((output / "passport.json").is_file())
        self.assertTrue((output / "capture-packet").is_dir())
        self.assertTrue((output / "run-package.json").is_file())
        self.assertTrue((output / "README_RUN.md").is_file())

    def test_unverified_attestation_blocks_package_creation(self):
        output = self.root / "run-package"
        with (
            patch("tools.ai_visibility_prepare_run.load_module", return_value={"schema": "test-module"}),
            patch("tools.ai_visibility_prepare_run.validate_attestation", return_value=(["missing independent review"], "PENDING_REVIEW")),
        ):
            with self.assertRaisesRegex(ValueError, "not VERIFIED"):
                prepare_run(self.module, self.attestation, "run-001", output)
        self.assertFalse(output.exists())

    def test_existing_output_is_never_overwritten(self):
        output = self.root / "run-package"
        output.mkdir()
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            prepare_run(self.module, self.attestation, "run-001", output)


if __name__ == "__main__":
    unittest.main()
