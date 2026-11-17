import csv
import json
import tempfile
import unittest
from pathlib import Path
from tools.ai_visibility_evidence import SCORE_KEYS, validate_batch, validate_record

def make_record(**updates):
    record = {
        "schema": "studio/ai-visibility-observation/1",
        "observation_id": "obs-001",
        "run_id": "run-001",
        "observed_at_utc": "2026-11-17T15:00:00Z",
        "market": {"country_code": "RU", "interface_locale": "ru-RU", "prompt_language": "ru", "answer_language": "ru", "region": "Moscow", "region_evidence": "Product region selector"},
        "platform": {"id": "yandex_alice_ai", "product": "Alice AI", "surface": "Alice AI consumer interface", "measurement_mode": "consumer_ui"},
        "query": {"query_id": "RU-GEN-AD-01", "intent": "generic_commercial", "exact_prompt": "Где заказать рекламный аудиоролик?"},
        "answer_status": "OK",
        "raw_answer": "Полный сохранённый ответ.",
        "answer_excerpt": "Краткий фрагмент.",
        "named_providers": [],
        "generic_discovery_hit": False,
        "critical_error": False,
        "scores": {key: None for key in SCORE_KEYS},
        "evidence": {"sources": [], "repository_files": [], "capture_artifact": None},
        "limitations": [],
        "operator_notes": None,
    }
    record.update(updates)
    return record

class EvidenceRecordTests(unittest.TestCase):
    def test_valid_full_answer_record_passes(self):
        self.assertEqual(validate_record(make_record()), [])

    def test_answered_record_requires_full_answer(self):
        errors = validate_record(make_record(raw_answer="  "))
        self.assertTrue(any("complete raw_answer" in item for item in errors))

    def test_blocked_record_cannot_carry_scores_or_hit(self):
        record = make_record(answer_status="BLOCKED_REGION", raw_answer="", generic_discovery_hit=None, critical_error=None)
        record["scores"]["brand_identity"] = 0
        errors = validate_record(record)
        self.assertTrue(any("cannot carry numeric scores" in item for item in errors))

    def test_non_utc_timestamp_fails(self):
        errors = validate_record(make_record(observed_at_utc="2026-11-17T15:00:00+02:00"))
        self.assertTrue(any("UTC timestamp" in item for item in errors))

    def test_invalid_source_url_fails(self):
        record = make_record(evidence={"sources": [{"url": "not-a-url"}]})
        errors = validate_record(record)
        self.assertTrue(any("absolute HTTP(S) URL" in item for item in errors))

    def test_batch_requires_csv_link_and_matching_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            record = make_record()
            (records / "obs-001.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            csv_path = root / "benchmark.csv"
            headers = ["observation_id", "run_id", "country_code", "interface_locale", "platform", "measurement_mode", "query_id", "answer_status"]
            row = {"observation_id": "obs-001", "run_id": "run-001", "country_code": "RU", "interface_locale": "ru-RU", "platform": "yandex_alice_ai", "measurement_mode": "consumer_ui", "query_id": "RU-GEN-AD-01", "answer_status": "OK"}
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=headers)
                writer.writeheader()
                writer.writerow(row)
            self.assertEqual(validate_batch(records, csv_path), [])
            row["platform"] = "gemini"
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=headers)
                writer.writeheader()
                writer.writerow(row)
            errors = validate_batch(records, csv_path)
            self.assertTrue(any("platform does not match" in item for item in errors))

if __name__ == "__main__":
    unittest.main()
