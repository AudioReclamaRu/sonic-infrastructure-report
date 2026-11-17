import csv
import tempfile
import unittest
from pathlib import Path

from tools.ai_visibility_coverage import analyze, render_markdown

QUEUE_FIELDS = [
    "queue_id", "module_id", "module_version", "query_id", "query", "intent",
    "country_code", "interface_locale", "prompt_language", "answer_language",
    "platform", "platform_surface", "measurement_mode", "platform_priority",
    "execution_status", "region_verification", "notes",
]
OBS_FIELDS = [
    "run_id", "country_code", "interface_locale", "prompt_language", "answer_language",
    "platform", "platform_surface", "measurement_mode", "intent", "query_id",
    "answer_status", "observation_id",
]


def queue_row(query="Q1", platform="chatgpt", intent="commercial"):
    return dict(zip(QUEUE_FIELDS, [
        f"{query}-{platform}", "module/1", "1.0", query, "prompt", intent,
        "RU", "ru-RU", "ru", "ru", platform, "consumer UI", "consumer_ui",
        "1", "NOT_TESTED", "UNVERIFIED", "",
    ]))


def observation(query="Q1", platform="chatgpt", status="OK", oid="obs-1", intent="commercial"):
    return {
        "run_id": "run-1", "country_code": "RU", "interface_locale": "ru-RU",
        "prompt_language": "ru", "answer_language": "ru", "platform": platform,
        "platform_surface": "consumer UI", "measurement_mode": "consumer_ui",
        "intent": intent, "query_id": query, "answer_status": status, "observation_id": oid,
    }


class CoverageAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write_csv(self, name, fields, rows):
        path = self.root / name
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_reports_missing_planned_cells_and_dimension_breakdowns(self):
        queue = self.write_csv("queue.csv", QUEUE_FIELDS, [
            queue_row(), queue_row(query="Q2", platform="gemini", intent="expertise")
        ])
        obs = self.write_csv("obs.csv", OBS_FIELDS, [observation()])
        report = analyze([queue], obs)
        self.assertEqual(report["totals"]["planned_cells"], 2)
        self.assertEqual(report["totals"]["observed_cells"], 1)
        self.assertEqual(report["totals"]["missing_cells"], 1)
        self.assertEqual(report["coverage"]["by_platform"][1]["missing_cells"], 1)
        self.assertEqual(report["missing_cells"][0]["query_id"], "Q2")

    def test_blocked_is_collection_coverage_not_zero_visibility(self):
        queue = self.write_csv("queue.csv", QUEUE_FIELDS, [queue_row()])
        obs = self.write_csv("obs.csv", OBS_FIELDS, [
            observation(status="BLOCKED_REGION")
        ])
        report = analyze([queue], obs)
        self.assertEqual(report["totals"]["observed_cells"], 1)
        self.assertEqual(report["totals"]["non_answer_rows"], 1)
        self.assertEqual(report["totals"]["answered_rows"], 0)
        self.assertIn("never as zero visibility", " ".join(report["interpretation"]))

    def test_rejects_completed_status_in_planning_queue(self):
        row = queue_row()
        row["execution_status"] = "OK"
        queue = self.write_csv("queue.csv", QUEUE_FIELDS, [row])
        report = analyze([queue])
        self.assertTrue(any("must remain NOT_TESTED" in e for e in report["errors"]))

    def test_rejects_duplicate_planned_cell(self):
        row = queue_row()
        duplicate = dict(row, queue_id="another-id")
        queue = self.write_csv("queue.csv", QUEUE_FIELDS, [row, duplicate])
        report = analyze([queue])
        self.assertTrue(any("duplicate planned cell" in e for e in report["errors"]))

    def test_rejects_observation_outside_plan_and_duplicate_id(self):
        queue = self.write_csv("queue.csv", QUEUE_FIELDS, [queue_row()])
        obs = self.write_csv("obs.csv", OBS_FIELDS, [
            observation(oid="same"), observation(query="QX", oid="same")
        ])
        report = analyze([queue], obs)
        self.assertTrue(any("no matching planned cell" in e for e in report["errors"]))
        self.assertTrue(any("duplicate observation_id" in e for e in report["errors"]))

    def test_markdown_is_standalone_and_shows_scope(self):
        queue = self.write_csv("queue.csv", QUEUE_FIELDS, [queue_row()])
        report = analyze([queue])
        markdown = render_markdown(report)
        self.assertIn("AI Visibility Coverage Report", markdown)
        self.assertIn("Collection coverage", markdown)
        self.assertIn("NOT", " ".join(report["interpretation"]))


if __name__ == "__main__":
    unittest.main()
