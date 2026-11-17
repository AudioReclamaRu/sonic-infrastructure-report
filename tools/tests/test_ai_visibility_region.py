import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.ai_visibility_region import validate_attestation


class RegionAttestationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.files = {}
        for name, body in {
            "geo-a.txt": "provider A says RU",
            "geo-b.txt": "provider B says RU",
            "asn.txt": "local ISP registry evidence",
            "session.png": "synthetic UI capture fixture",
        }.items():
            path = self.root / name
            path.write_text(body, encoding="utf-8")
            self.files[name] = {
                "evidence_file": name,
                "evidence_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        self.record = {
            "schema": "studio/ai-visibility-region-attestation/1",
            "attestation_id": "ru-test-001",
            "observed_at_utc": "2026-11-17T12:00:00Z",
            "country_code": "RU",
            "interface_locale": "ru-RU",
            "network": {
                "connection_type": "residential_isp",
                "vpn_detected": False,
                "proxy_detected": False,
                "remote_desktop_detected": False,
                "ip_fingerprint_sha256": "a" * 64,
                "provider_name": "Example Local ISP",
            },
            "geolocation_sources": [
                {
                    "provider": "Geo Provider A", "independence_group": "geo-vendor-a",
                    "country_code": "RU", "captured_at_utc": "2026-11-17T12:02:00Z",
                    **self.files["geo-a.txt"],
                },
                {
                    "provider": "Geo Provider B", "independence_group": "geo-vendor-b",
                    "country_code": "RU", "captured_at_utc": "2026-11-17T12:03:00Z",
                    **self.files["geo-b.txt"],
                },
            ],
            "network_owner_evidence": {
                "provider": "ASN Registry", "organization": "Example Local ISP",
                "network_class": "residential_isp", **self.files["asn.txt"],
            },
            "session_capture": {
                "platform": "ChatGPT", "product": "Consumer UI",
                "interface_locale": "ru-RU", "captured_at_utc": "2026-11-17T12:04:00Z",
                **self.files["session.png"],
            },
            "operator_declaration": {
                "operator": "operator-a", "direct_connection": True,
                "no_vpn": True, "no_proxy": True, "no_remote_desktop": True,
            },
            "review": {
                "status": "APPROVED", "reviewer": "reviewer-b",
                "reviewed_at_utc": "2026-11-17T13:00:00Z",
                "rationale": "Independent review of the attached evidence pack.",
            },
        }

    def test_complete_independently_reviewed_pack_is_verified(self):
        errors, status = validate_attestation(self.record, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(status, "VERIFIED")

    def test_pending_review_is_not_verified(self):
        self.record["review"] = {"status": "PENDING"}
        errors, status = validate_attestation(self.record, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(status, "PENDING_REVIEW")

    def test_vpn_or_proxy_blocks_ru_baseline(self):
        self.record["network"]["vpn_detected"] = True
        errors, status = validate_attestation(self.record, self.root)
        self.assertTrue(any("vpn_detected must be false" in item for item in errors))
        self.assertEqual(status, "EVIDENCE_INCOMPLETE")

    def test_two_geolocation_sources_must_be_independent(self):
        self.record["geolocation_sources"][1]["independence_group"] = "geo-vendor-a"
        errors, status = validate_attestation(self.record, self.root)
        self.assertTrue(any("distinct independence_group" in item for item in errors))
        self.assertEqual(status, "EVIDENCE_INCOMPLETE")

    def test_artifact_tampering_is_detected(self):
        (self.root / "geo-a.txt").write_text("changed", encoding="utf-8")
        errors, status = validate_attestation(self.record, self.root)
        self.assertTrue(any("SHA-256 mismatch" in item for item in errors))
        self.assertEqual(status, "EVIDENCE_INCOMPLETE")

    def test_operator_cannot_approve_their_own_attestation(self):
        self.record["review"]["reviewer"] = "operator-a"
        errors, status = validate_attestation(self.record, self.root)
        self.assertTrue(any("independent from the operator" in item for item in errors))
        self.assertEqual(status, "EVIDENCE_INCOMPLETE")

    def test_raw_ip_field_is_rejected(self):
        self.record["network"]["ip_address"] = "203.0.113.10"
        errors, status = validate_attestation(self.record, self.root)
        self.assertTrue(any("raw IP addresses" in item for item in errors))
        self.assertEqual(status, "EVIDENCE_INCOMPLETE")

    def test_stale_geolocation_evidence_is_rejected(self):
        self.record["geolocation_sources"][0]["captured_at_utc"] = "2026-11-17T10:00:00Z"
        errors, status = validate_attestation(self.record, self.root)
        self.assertTrue(any("within 30 minutes" in item for item in errors))
        self.assertEqual(status, "EVIDENCE_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
