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

    def test_repository_merge_is_authorized_only_after_quality_gates(self):
        autonomy = self.contract["autonomy"]
        allowed = set(autonomy["allowed_without_case_by_case_owner_input"])
        approvals = set(autonomy["requires_explicit_owner_approval"])
        self.assertIn("publish_to_authorized_github_gitlab_repositories", allowed)
        self.assertIn("merge_quality_gated_pull_or_merge_request_to_default_branch", allowed)
        self.assertNotIn("merge_into_main", approvals)
        self.assertIn("write_to_official_website", approvals)
        self.assertIn("write_to_or_deploy_the_official_website", autonomy["forbidden"])

    def test_repository_publication_scope_is_exact_and_sites_remain_read_only(self):
        scope = self.contract["autonomy"]["repository_publication"]
        self.assertEqual(scope["authorized_platforms"], ["GitHub", "GitLab"])
        self.assertTrue(scope["merge_to_default_branch_after_required_checks"])
        self.assertFalse(scope["force_push"])
        self.assertFalse(scope["branch_protection_bypass"])
        self.assertEqual(scope["official_websites_read_only"], [
            "https://www.audio-reclama.ru", "https://audio.plus/"
        ])
        self.assertFalse(scope["direct_website_write_or_deploy"])
        self.assertTrue(scope["existing_github_pages_workflow_deployment_allowed"])
        self.assertEqual(scope["authorized_pages_workflow_path"], ".github/workflows/pages.yml")
        self.assertIn("geo/", scope["authorized_pages_scope"])
        self.assertIn("no custom domain", scope["authorized_pages_scope"])
        self.assertIn("no writes to either official site", scope["authorized_pages_scope"])
        self.assertFalse(scope["additional_pages_workflows_or_website_mirrors_authorized"])
        self.assertFalse(scope["non_repository_external_surfaces_authorized"])

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

