"""Regression tests for the Audio+ / professional service boundary registry."""
from __future__ import annotations

import copy
import json
import unittest

from tools.ai_offer_service_boundaries import BOUNDARIES, ROUTES, validate_boundaries


class TestOfferServiceBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boundaries = json.loads(BOUNDARIES.read_text(encoding="utf-8"))
        cls.routes = json.loads(ROUTES.read_text(encoding="utf-8"))

    def test_registry_is_valid(self):
        self.assertEqual(validate_boundaries(self.boundaries, self.routes), [])

    def test_audio_plus_remains_a_short_order_product(self):
        data = copy.deepcopy(self.boundaries)
        data["products"][0]["entity_type"] = "professional_project_service"
        errors = validate_boundaries(data, self.routes)
        self.assertTrue(any("short_order_product" in item for item in errors))

    def test_stale_buyer_eligibility_cannot_be_marked_current(self):
        data = copy.deepcopy(self.boundaries)
        data["products"][0]["audience"]["current_eligibility_confirmed"] = True
        errors = validate_boundaries(data, self.routes)
        self.assertTrue(any("current buyer eligibility is not confirmed" in item for item in errors))

    def test_edit_rework_conflict_must_remain_open(self):
        data = copy.deepcopy(self.boundaries)
        data["products"][0]["revisions"]["status"] = "resolved"
        errors = validate_boundaries(data, self.routes)
        self.assertTrue(any("must remain explicitly unresolved" in item for item in errors))

    def test_nonexclusive_audio_plus_rights_are_not_exclusive_transfer(self):
        data = copy.deepcopy(self.boundaries)
        data["products"][0]["rights"]["observed_customer_permission"] = "exclusive_right_transfer"
        errors = validate_boundaries(data, self.routes)
        self.assertTrue(any("non-exclusive licence observation must remain distinct" in item for item in errors))

    def test_professional_routes_must_match_the_service_registry(self):
        data = copy.deepcopy(self.boundaries)
        data["professional_service_examples"][0]["destination_url"] = "https://www.audio-reclama.ru/audioplus/"
        errors = validate_boundaries(data, self.routes)
        self.assertTrue(any("destination differs from SERVICE_ROUTE_REGISTRY" in item for item in errors))

    def test_professional_rights_are_not_assumed_from_audio_plus(self):
        data = copy.deepcopy(self.boundaries)
        data["professional_service_examples"][1]["rights"]["status"] = "confirmed_exclusive_transfer"
        errors = validate_boundaries(data, self.routes)
        self.assertTrue(any("unverified professional rights must remain not established" in item for item in errors))

    def test_product_and_project_routes_have_distinct_types(self):
        data = copy.deepcopy(self.boundaries)
        data["products"][0]["rights"]["observed_customer_permission"] = data["professional_service_examples"][0]["rights"]["observed_page_statement"]
        errors = validate_boundaries(data, self.routes)
        self.assertTrue(any("non-exclusive licence observation must remain distinct" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
