import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ai_visibility_prepare_run import _copy_region_inputs, prepare_run


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
            patch("tools.ai_visibility_prepare_run.build_packet", side_effect=lambda _passport, path: (path.mkdir(parents=True), {"schema": "packet/1", "planned_cells": 1})[1]),
        ):
            manifest = prepare_run(self.module, self.attestation, "run-001", output)
        self.assertEqual(manifest["package_status"], "PLANNED_CAPTURE_READY")
        self.assertTrue((output / "queue.csv").is_file())
        self.assertTrue((output / "passport.json").is_file())
        self.assertTrue((output / "capture-packet").is_dir())
        self.assertTrue((output / "run-package.json").is_file())
        self.assertTrue((output / "README_RUN.md").is_file())
        self.assertEqual((output / "inputs/query-module/queries.json").read_text(encoding="utf-8"), '{"schema":"test-module"}')
        self.assertEqual((output / "inputs/region-attestation/attestation.json").read_bytes(), self.attestation.read_bytes())


    def test_copies_attestation_evidence_without_rewriting_source(self):
        evidence_dir = self.root / "evidence"
        evidence_dir.mkdir()
        evidence = evidence_dir / "session.png"
        evidence.write_bytes(b"session-evidence")
        attestation = {
            "attestation_id": "attestation-001",
            "session_capture": {"evidence_file": "evidence/session.png"},
        }
        self.attestation.write_text(json.dumps(attestation), encoding="utf-8")
        output = self.root / "portable-run"
        with (
            patch("tools.ai_visibility_prepare_run.load_module", return_value={"schema": "test-module"}),
            patch("tools.ai_visibility_prepare_run.validate_attestation", return_value=([], "VERIFIED")),
            patch("tools.ai_visibility_prepare_run.build_rows", return_value=[{"queue_id": "Q1"}]),
            patch("tools.ai_visibility_prepare_run.write_queue", side_effect=lambda _rows, path: path.write_text("queue fixture", encoding="utf-8")),
            patch("tools.ai_visibility_prepare_run.create_plan", return_value={"run_id": "run-001", "passport_sha256": "a" * 64}),
            patch("tools.ai_visibility_prepare_run.validate_plan", return_value=([], {"run_id": "run-001", "passport_sha256": "a" * 64})),
            patch("tools.ai_visibility_prepare_run.build_packet", side_effect=lambda _passport, path: (path.mkdir(parents=True), {"schema": "packet/1", "planned_cells": 1})[1]),
        ):
            prepare_run(self.module, self.attestation, "run-001", output)
        copied = output / "inputs/region-attestation/evidence/session.png"
        self.assertEqual(copied.read_bytes(), b"session-evidence")
        self.assertEqual(self.attestation.read_text(encoding="utf-8"), json.dumps(attestation))


    def test_unverified_attestation_blocks_package_creation(self):
        output = self.root / "run-package"
        with (
            patch("tools.ai_visibility_prepare_run.load_module", return_value={"schema": "test-module"}),
            patch("tools.ai_visibility_prepare_run.validate_attestation", return_value=(["missing independent review"], "PENDING_REVIEW")),
        ):
            with self.assertRaisesRegex(ValueError, "not VERIFIED"):
                prepare_run(self.module, self.attestation, "run-001", output)
        self.assertFalse(output.exists())

    def test_rejects_attestation_evidence_path_escape(self):
        target = self.root / "snapshot"
        with self.assertRaisesRegex(ValueError, "must stay inside"):
            _copy_region_inputs(
                {"session_capture": {"evidence_file": "../outside.png"}},
                self.root,
                target,
            )
        self.assertFalse(target.exists())

    def test_existing_output_is_never_overwritten(self):
        output = self.root / "run-package"
        output.mkdir()
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            prepare_run(self.module, self.attestation, "run-001", output)


if __name__ == "__main__":
    unittest.main()
