"""Regression tests for the Megabrain AI Discoverability handoff contract."""
from __future__ import annotations

import json
import unittest

from tools.ai_discoverability_contract import (
    CONTRACT, QUEUE, validate_contract, validate_queue,
)


class TestMegabrainDiscoverabilityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.queue = json.loads(QUEUE.read_text(encoding="utf-8"))

    def test_contract_and_queue_are_valid(self):
        self.assertEqual(validate_contract(self.contract), [])
        self.assertEqual(validate_queue(self.queue), [])

    def test_owner_is_not_required_to_collect_data(self):
        self.assertTrue(self.contract["execution_policy"]["must_not_require_owner_to_collect_or_upload_data"])

    def test_main_merge_and_website_writes_are_gated(self):
        approvals = set(self.contract["autonomy"]["requires_explicit_owner_approval"])
        self.assertIn("merge_into_main", approvals)
        self.assertIn("write_to_official_website", approvals)

    def test_measurement_without_stop_guard_fails(self):
        queue = json.loads(json.dumps(self.queue))
        queue["items"][1]["measurement_guard"]["stop_rule"] = ""
        self.assertTrue(any("measurement_guard" in e for e in validate_queue(queue)))

    def test_done_without_validation_fails(self):
        queue = json.loads(json.dumps(self.queue))
        queue["items"][0]["status"] = "done"
        # Build the negative case locally: a closed queue item may legitimately
        # carry validation references, so the fixture must clear them itself.
        queue["items"][0]["validation_refs"] = []
        self.assertTrue(any("done requires validation_refs" in e for e in validate_queue(queue)))

    def test_duplicate_work_id_fails(self):
        queue = json.loads(json.dumps(self.queue))
        queue["items"].append(json.loads(json.dumps(queue["items"][0])))
        self.assertTrue(any("duplicate work item id" in e for e in validate_queue(queue)))

    def test_blocked_work_needs_unblock_condition(self):
        queue = json.loads(json.dumps(self.queue))
        queue["items"][1]["unblock_condition"] = None
        self.assertTrue(any("blocked work requires blocker" in e for e in validate_queue(queue)))


if __name__ == "__main__":
    unittest.main()
