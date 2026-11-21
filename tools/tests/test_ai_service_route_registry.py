"""Regression tests for the repository service-route registry."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.ai_service_route_registry import REGISTRY, ROOT, validate_registry


class TestServiceRouteRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_repository_route_registry_is_valid(self):
        self.assertEqual(validate_registry(self.registry, ROOT), [])

    def test_route_ids_must_be_unique(self):
        data = copy.deepcopy(self.registry)
        data["routes"].append(copy.deepcopy(data["routes"][0]))
        self.assertTrue(any("duplicate route id" in item for item in validate_registry(data, ROOT)))

    def test_noncanonical_host_is_rejected(self):
        data = copy.deepcopy(self.registry)
        data["routes"][0]["destination_url"] = "https://example.com/voices/"
        errors = validate_registry(data, ROOT)
        self.assertTrue(any("canonical HTTPS host" in item for item in errors))

    def test_professional_route_cannot_default_to_audio_plus(self):
        data = copy.deepcopy(self.registry)
        data["routes"][2]["destination_url"] = "https://www.audio-reclama.ru/audioplus/"
        errors = validate_registry(data, ROOT)
        self.assertTrue(any("cannot default to the separate Audio+" in item for item in errors))

    def test_service_destination_must_exist_in_a_source_guide(self):
        data = copy.deepcopy(self.registry)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "guides").mkdir()
            (root / "guides/source.md").write_text("# No destination link here", encoding="utf-8")
            route = copy.deepcopy(data["routes"][0])
            route["source_guides"] = ["guides/source.md"]
            data["routes"] = [route]
            errors = validate_registry(data, root)
        self.assertTrue(any("destination URL is not referenced" in item for item in errors))

    def test_audio_plus_exclusion_requires_fresh_offer_check(self):
        data = copy.deepcopy(self.registry)
        data["product_boundaries"][0]["current_offer_recheck_required"] = False
        errors = validate_registry(data, ROOT)
        self.assertTrue(any("current offer must be rechecked" in item for item in errors))

    def test_read_only_and_no_deploy_policy_is_fail_closed(self):
        data = copy.deepcopy(self.registry)
        data["policy"]["github_pages_deployment_authorized"] = True
        errors = validate_registry(data, ROOT)
        self.assertTrue(any("policy.github_pages_deployment_authorized" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
