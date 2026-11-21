"""Regression tests for the official service-route Search Console snapshot."""
from __future__ import annotations
import copy
import json
import unittest
from tools.validate_service_route_searchconsole import SNAPSHOT, ROUTES, validate

class TestServiceRouteSearchConsole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        cls.routes = json.loads(ROUTES.read_text(encoding="utf-8"))

    def test_snapshot_is_valid(self):
        self.assertEqual(validate(self.data, self.routes), [])

    def test_totals_must_reconcile(self):
        data = copy.deepcopy(self.data)
        data['page_level_totals']['clicks'] += 1
        self.assertTrue(any('do not reconcile' in e for e in validate(data, self.routes)))

    def test_unknown_route_is_rejected(self):
        data = copy.deepcopy(self.data)
        data['pages'][0]['route_id'] = 'legacy_geo_answer'
        self.assertTrue(any('not a professional service route' in e for e in validate(data, self.routes)))

    def test_legacy_page_performance_must_not_be_inferred(self):
        data = copy.deepcopy(self.data)
        data['scope']['route_metrics_do_not_measure_legacy_answer_url_performance'] = False
        self.assertTrue(any('must not be attributed' in e for e in validate(data, self.routes)))

    def test_paid_history_limit_must_be_disclosed(self):
        data = copy.deepcopy(self.data)
        data['source']['long_range_attempt']['status'] = 'allowed'
        self.assertTrue(any('data-access limitation' in e for e in validate(data, self.routes)))

    def test_empty_ga4_must_not_mean_zero_traffic(self):
        data = copy.deepcopy(self.data)
        data['cross_source_check']['interpretation'] = 'zero traffic'
        self.assertTrue(any('zero traffic' in e for e in validate(data, self.routes)))

if __name__ == '__main__':
    unittest.main()
