import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.ai_visibility_package import validate_package
from tools.ai_visibility_prepare_run import prepare_run


class RunPackageAuditTests(unittest.TestCase):
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
        self.attestation = self._make_attestation()
        self.attestation_path = self.root / "attestation.json"
        self.attestation_path.write_text(json.dumps(self.attestation), encoding="utf-8")
        self.package_dir = self.root / "portable-run"
        prepare_run(self.module, self.attestation_path, "audit-run-001", self.package_dir)

    def _make_attestation(self):
        artifacts = {}
        for name, body in {
            "geo-a.txt": "synthetic geo provider A",
            "geo-b.txt": "synthetic geo provider B",
            "asn.txt": "synthetic ISP registry",
            "session.txt": "synthetic session capture",
        }.items():
            path = self.root / name
            path.write_text(body, encoding="utf-8")
            artifacts[name] = {
                "evidence_file": name,
                "evidence_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        return {
            "schema": "studio/ai-visibility-region-attestation/1",
            "attestation_id": "synthetic-package-audit-attestation",
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
                "provider": "Synthetic ASN registry", "organization": "Synthetic ISP",
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
                "rationale": "Synthetic fixture for automated package audit tests only.",
            },
        }

    def test_complete_portable_package_passes_audit(self):
        errors, manifest = validate_package(self.package_dir / "run-package.json")
        self.assertEqual(errors, [])
        self.assertEqual(manifest["run_id"], "audit-run-001")

    def test_tampered_regional_evidence_fails_audit(self):
        evidence = self.package_dir / "inputs/region-attestation/session.txt"
        evidence.write_text("tampered", encoding="utf-8")
        errors, _ = validate_package(self.package_dir / "run-package.json")
        self.assertTrue(any("SHA-256 mismatch" in error or "evidence SHA-256 mismatch" in error for error in errors), errors)

    def test_completed_capture_template_fails_draft_package_audit(self):
        packet = self.package_dir / "capture-packet"
        manifest = json.loads((packet / "capture-manifest.json").read_text(encoding="utf-8"))
        template = packet / manifest["evidence_templates"][0]
        record = json.loads(template.read_text(encoding="utf-8"))
        record["answer_status"] = "OK"
        template.write_text(json.dumps(record), encoding="utf-8")
        errors, _ = validate_package(self.package_dir / "run-package.json")
        self.assertTrue(any("NOT_TESTED" in error for error in errors), errors)

    def test_package_manifest_rejects_path_escape(self):
        manifest_path = self.package_dir / "run-package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["queue"]["path"] = "../outside.csv"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        errors, _ = validate_package(manifest_path)
        self.assertTrue(any("unsafe package-relative path" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
