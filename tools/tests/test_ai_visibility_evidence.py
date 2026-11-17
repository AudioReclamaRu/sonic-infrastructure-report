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
    def _attestation_binding(self):
        return {
            "attestation_id": "attestation-001",
            "sha256": "a" * 64,
            "session_captured_at_utc": "2026-11-17T15:00:00Z",
        }

    def _bind_record(self, record):
        record["market"]["region_attestation_id"] = "attestation-001"
        record["market"]["region_attestation_sha256"] = "a" * 64
        return record

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
            headers = ["observation_id", "run_id", "country_code", "interface_locale", "prompt_language", "answer_language", "platform", "platform_surface", "measurement_mode", "query_id", "intent", "query", "answer_status"]
            row = {"observation_id": "obs-001", "run_id": "run-001", "country_code": "RU", "interface_locale": "ru-RU", "prompt_language": "ru", "answer_language": "ru", "platform": "yandex_alice_ai", "platform_surface": "Alice AI consumer interface", "measurement_mode": "consumer_ui", "query_id": "RU-GEN-AD-01", "intent": "generic_commercial", "query": "Где заказать рекламный аудиоролик?", "answer_status": "OK"}
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


    def _write_queue(self, root, prompt="Где заказать рекламный аудиоролик?", region_status="VERIFIED"):
        path = root / "queue.csv"
        fields = [
            "query_id", "query", "intent", "country_code", "interface_locale",
            "prompt_language", "answer_language", "platform", "platform_surface",
            "measurement_mode", "execution_status", "region_verification",
        ]
        row = {
            "query_id": "RU-GEN-AD-01", "query": prompt, "intent": "generic_commercial",
            "country_code": "RU", "interface_locale": "ru-RU", "prompt_language": "ru",
            "answer_language": "ru", "platform": "yandex_alice_ai",
            "platform_surface": "Alice AI consumer interface", "measurement_mode": "consumer_ui",
            "execution_status": "NOT_TESTED", "region_verification": region_status,
        }
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
        return path

    def test_batch_requires_exact_queue_cell_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            record = self._bind_record(make_record())
            (records / "obs-001.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            queue = self._write_queue(root)
            binding = self._attestation_binding()
            self.assertEqual(validate_batch(records, queue_path=queue, expected_region_attestation=binding), [])
            wrong_queue = self._write_queue(root, prompt="Другой точный запрос")
            errors = validate_batch(records, queue_path=wrong_queue, expected_region_attestation=binding)
            self.assertTrue(any("no exact matching planned queue cell" in item for item in errors))


    def test_batch_matches_across_multiple_frozen_queues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            record = self._bind_record(make_record())
            (records / "obs-001.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            matching = self._write_queue(root)
            matching.rename(root / "queue-matching.csv")
            nonmatching = self._write_queue(root, prompt="Another exact prompt")
            errors = validate_batch(
                records,
                queue_paths=[root / "queue-matching.csv", nonmatching],
                expected_region_attestation=self._attestation_binding(),
            )
            self.assertEqual(errors, [])

    def test_unverified_region_is_never_promoted_by_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            (records / "obs-001.json").write_text(json.dumps(make_record(), ensure_ascii=False), encoding="utf-8")
            queue = self._write_queue(root, region_status="UNVERIFIED")
            errors = validate_batch(records, queue_path=queue)
            self.assertTrue(any("region is UNVERIFIED" in item for item in errors))


    def test_verified_region_requires_explicit_primary_record_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            record = self._bind_record(make_record())
            record["market"]["region_evidence"] = ""
            (records / "obs-001.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            queue = self._write_queue(root, region_status="VERIFIED")
            errors = validate_batch(records, queue_path=queue, expected_region_attestation=self._attestation_binding())
            self.assertTrue(any("VERIFIED region requires explicit" in item for item in errors))

    def test_non_answer_csv_row_requires_primary_json_observation_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            queue = self._write_queue(root)
            blocked = make_record(
                answer_status="BLOCKED_REGION", raw_answer="",
                generic_discovery_hit=None, critical_error=None,
            )
            (records / "obs-blocked.json").write_text(json.dumps(blocked), encoding="utf-8")
            csv_path = root / "benchmark.csv"
            headers = [
                "observation_id", "run_id", "country_code", "interface_locale",
                "prompt_language", "answer_language", "platform", "platform_surface",
                "measurement_mode", "query_id", "intent", "query", "answer_status",
            ]
            row = {
                "observation_id": "", "run_id": "run-001", "country_code": "RU",
                "interface_locale": "ru-RU", "prompt_language": "ru", "answer_language": "ru",
                "platform": "yandex_alice_ai", "platform_surface": "Alice AI consumer interface",
                "measurement_mode": "consumer_ui", "query_id": "RU-GEN-AD-01",
                "intent": "generic_commercial", "query": "Где заказать рекламный аудиоролик?",
                "answer_status": "BLOCKED_REGION",
            }
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=headers)
                writer.writeheader()
                writer.writerow(row)
            errors = validate_batch(records, csv_path, queue_path=queue)
            self.assertTrue(any("every collection outcome requires observation_id" in e for e in errors))

    def test_unlinked_non_answer_csv_row_cannot_be_added_beside_valid_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            record = make_record()
            (records / "obs-001.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            csv_path = root / "benchmark.csv"
            headers = [
                "observation_id", "run_id", "country_code", "interface_locale",
                "prompt_language", "answer_language", "platform", "platform_surface",
                "measurement_mode", "query_id", "intent", "query", "answer_status",
            ]
            base = {
                "observation_id": "obs-001", "run_id": "run-001", "country_code": "RU",
                "interface_locale": "ru-RU", "prompt_language": "ru", "answer_language": "ru",
                "platform": "yandex_alice_ai", "platform_surface": "Alice AI consumer interface",
                "measurement_mode": "consumer_ui", "query_id": "RU-GEN-AD-01",
                "intent": "generic_commercial", "query": "Где заказать рекламный аудиоролик?",
                "answer_status": "OK",
            }
            phantom = dict(base, observation_id="", answer_status="BLOCKED_REGION")
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=headers)
                writer.writeheader()
                writer.writerow(base)
                writer.writerow(phantom)
            errors = validate_batch(records, csv_path)
            self.assertTrue(any("every collection outcome requires observation_id" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
