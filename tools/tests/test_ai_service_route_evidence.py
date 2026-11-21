"""Regression tests for source freshness and evidence boundaries of service routes."""
from __future__ import annotations

import copy
import json
import unittest

from tools.ai_service_route_evidence import MATRIX, ROUTES, validate_matrix


class TestServiceRouteEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.routes = json.loads(ROUTES.read_text(encoding="utf-8"))

    def test_repository_evidence_matrix_is_valid(self):
        self.assertEqual(validate_matrix(self.matrix, self.routes), [])

    def test_every_professional_route_is_covered_once(self):
        data = copy.deepcopy(self.matrix)
        data["routes"].pop()
        errors = validate_matrix(data, self.routes)
        self.assertTrue(any("missing from evidence matrix" in item for item in errors))

    def test_duplicate_route_evidence_is_rejected(self):
        data = copy.deepcopy(self.matrix)
        data["routes"].append(copy.deepcopy(data["routes"][0]))
        errors = validate_matrix(data, self.routes)
        self.assertTrue(any("duplicate route evidence id" in item for item in errors))

    def test_destinations_must_match_the_service_route_registry(self):
        data = copy.deepcopy(self.matrix)
        data["routes"][0]["destination_url"] = "https://www.audio-reclama.ru/audioplus/"
        errors = validate_matrix(data, self.routes)
        self.assertTrue(any("destination differs from SERVICE_ROUTE_REGISTRY" in item for item in errors))

    def test_cached_snapshot_cannot_be_promoted_to_current_scope(self):
        data = copy.deepcopy(self.matrix)
        data["routes"][0]["current_service_scope_confirmed"] = True
        errors = validate_matrix(data, self.routes)
        self.assertTrue(any("current service scope must remain unconfirmed" in item for item in errors))

    def test_cache_miss_is_not_an_http_status_or_outage(self):
        data = copy.deepcopy(self.matrix)
        video = next(x for x in data["routes"] if x["route_registry_id"] == "video_production")
        cache_miss = next(x for x in video["source_observations"] if x["retrieval_result"] == "cache_miss")
        cache_miss["reported_crawl_age"] = "last week"
        errors = validate_matrix(data, self.routes)
        self.assertTrue(any("cache miss must not carry a crawl age" in item for item in errors))

    def test_rights_terms_cannot_be_promoted_to_confirmed(self):
        data = copy.deepcopy(self.matrix)
        data["routes"][0]["current_rights_terms_confirmed"] = True
        errors = validate_matrix(data, self.routes)
        self.assertTrue(any("current rights terms must remain unconfirmed" in item for item in errors))

    def test_live_http_and_form_state_remain_not_tested(self):
        data = copy.deepcopy(self.matrix)
        data["routes"][0]["live_http_status"] = "200"
        errors = validate_matrix(data, self.routes)
        self.assertTrue(any("live HTTP status must remain NOT_TESTED" in item for item in errors))

    def test_professional_routes_never_use_audio_plus_destinations(self):
        data = copy.deepcopy(self.matrix)
        data["routes"][0]["destination_url"] = "https://audio.plus/"
        errors = validate_matrix(data, self.routes)
        self.assertTrue(any("destination differs from SERVICE_ROUTE_REGISTRY" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
