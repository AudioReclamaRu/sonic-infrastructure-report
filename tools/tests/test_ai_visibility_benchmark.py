import csv
import tempfile
import unittest
from pathlib import Path
from tools.ai_visibility_benchmark import SCORE_FIELDS, summarize, validate

HEADERS = [
    "run_id", "date_utc", "date_time_utc", "country_code", "region",
    "interface_locale", "prompt_language", "answer_language", "platform",
    "product_or_model", "platform_surface", "measurement_mode", "mode",
    "search_mode", "grounding_state", "language", "auth_status", "query_id",
    "intent", "query", "answer_status", "completeness_status",
    *SCORE_FIELDS, "generic_discovery_hit", "critical_error", "cited_urls",
    "repository_file_cited", "competitors_mentioned", "answer_excerpt",
    "limitations", "operator_notes", "observation_id",
]

def make_row(**updates):
    row = {field: "" for field in HEADERS}
    row.update({
        "run_id": "run-001", "date_utc": "2026-11-17",
        "country_code": "RU", "interface_locale": "ru-RU",
        "prompt_language": "ru", "answer_language": "ru",
        "platform": "yandex_alice_ai", "platform_surface": "consumer",
        "measurement_mode": "consumer_ui", "intent": "generic_commercial",
        "query_id": "RU-GEN-AD-01", "query": "Где заказать рекламный аудиоролик?",
        "answer_status": "OK", "completeness_status": "complete",
        "brand_identity_score": "2", "official_route_score": "1",
        "generic_discovery_hit": "true", "observation_id": "obs-001",
    })
    row.update(updates)
    return row

class BenchmarkValidationTests(unittest.TestCase):
    def write_csv(self, rows):
        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        with handle:
            writer = csv.DictWriter(handle, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        return Path(handle.name)

    def test_valid_answer_row_passes(self):
        errors, rows = validate(self.write_csv([make_row()]))
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)

    def test_answered_row_requires_observation_id(self):
        errors, _ = validate(self.write_csv([make_row(observation_id="")]))
        self.assertTrue(any("require observation_id" in item for item in errors))

    def test_duplicate_observation_id_fails(self):
        errors, _ = validate(self.write_csv([make_row(), make_row(query_id="RU-GEN-AD-02", observation_id="obs-001")]))
        self.assertTrue(any("duplicate observation_id" in item for item in errors))

    def test_duplicate_observation_key_fails(self):
        errors, _ = validate(self.write_csv([make_row(), make_row()]))
        self.assertTrue(any("duplicate observation key" in item for item in errors))

    def test_score_outside_zero_to_two_fails(self):
        errors, _ = validate(self.write_csv([make_row(brand_identity_score="3")]))
        self.assertTrue(any("integer from 0 to 2" in item for item in errors))

    def test_blocked_row_cannot_be_scored(self):
        errors, _ = validate(self.write_csv([make_row(answer_status="BLOCKED_REGION", brand_identity_score="1", generic_discovery_hit="")]))
        self.assertTrue(any("cannot carry scores" in item for item in errors))

    def test_measurement_mode_must_be_explicit(self):
        errors, _ = validate(self.write_csv([make_row(measurement_mode="mixed")]))
        self.assertTrue(any("measurement_mode" in item for item in errors))

    def test_summary_keeps_consumer_and_api_separate(self):
        result = summarize([make_row(), make_row(measurement_mode="model_api", platform="claude")])
        self.assertEqual(len(result["groups"]), 2)
        self.assertEqual({g["measurement_mode"] for g in result["groups"]}, {"consumer_ui", "model_api"})

    def test_blocked_rows_are_not_zero_visibility(self):
        result = summarize([make_row(), make_row(platform="gemini", query_id="RU-GEN-AD-02", answer_status="BLOCKED_REGION", completeness_status="not_applicable", brand_identity_score="", official_route_score="", generic_discovery_hit="")])
        group = next(g for g in result["groups"] if g["platform"] == "gemini")
        self.assertEqual(group["answered"], 0)
        self.assertIsNone(group["generic_discovery_rate"])

if __name__ == "__main__":
    unittest.main()
