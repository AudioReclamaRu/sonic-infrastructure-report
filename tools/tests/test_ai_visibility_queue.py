import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.ai_visibility_queue import build_rows, validate_rows, write_queue, read_queue

def module_fixture():
    return {
        "schema": "test/module/1",
        "version": "1.0",
        "market": {
            "country_code": "RU", "interface_locale": "ru-RU",
            "prompt_language": "ru", "answer_language": "ru"
        },
        "platform_execution_order": [
            {"priority": 1, "id": "alice", "surface": "Alice consumer UI", "measurement_mode": "consumer_ui"},
            {"priority": 2, "id": "claude_api", "surface": "Claude API", "measurement_mode": "model_api"}
        ],
        "queries": [
            {"id": "Q1", "query": "Где заказать аудиоролик?", "intent": "generic_commercial", "brand_in_prompt": False},
            {"id": "Q2", "query": "Как выбрать диктора?", "intent": "expertise", "brand_in_prompt": False}
        ]
    }

class QueuePlannerTests(unittest.TestCase):
    def test_builds_complete_query_platform_product(self):
        rows = build_rows(module_fixture())
        self.assertEqual(len(rows), 4)
        self.assertEqual({r["measurement_mode"] for r in rows}, {"consumer_ui", "model_api"})
        self.assertEqual({r["execution_status"] for r in rows}, {"NOT_TESTED"})
        self.assertEqual({r["region_verification"] for r in rows}, {"UNVERIFIED"})
        self.assertEqual(validate_rows(rows, rows), [])

    def test_verified_region_status_is_explicit_and_separate_from_generation_default(self):
        rows = build_rows(module_fixture(), region_status="VERIFIED")
        self.assertEqual({r["region_verification"] for r in rows}, {"VERIFIED"})
        self.assertEqual(validate_rows(rows, rows), [])

    def test_rejects_mixed_or_unknown_measurement_mode(self):
        data = module_fixture()
        data["platform_execution_order"][0]["measurement_mode"] = "consumer_and_api"
        with self.assertRaisesRegex(ValueError, "measurement_mode"):
            build_rows(data)

    def test_rejects_duplicate_platform_ids(self):
        data = module_fixture()
        data["platform_execution_order"][1]["id"] = "alice"
        with self.assertRaisesRegex(ValueError, "duplicate platform"):
            build_rows(data)

    def test_rejects_duplicate_query_ids(self):
        data = module_fixture()
        data["queries"][1]["id"] = "Q1"
        with self.assertRaisesRegex(ValueError, "duplicate query"):
            build_rows(data)

    def test_generic_prompt_cannot_contain_brand_hint(self):
        data = module_fixture()
        data["queries"][0]["query"] = "Где заказать в " + "Аудио" + "-" + "Реклама?"
        with self.assertRaisesRegex(ValueError, "brand/domain hint"):
            build_rows(data)

    def test_queue_round_trip(self):
        rows = build_rows(module_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.csv"
            write_queue(rows, path)
            loaded = read_queue(path)
            self.assertEqual(loaded, rows)

    def test_missing_cartesian_pair_is_detected(self):
        rows = build_rows(module_fixture())[:-1]
        errors = validate_rows(rows, build_rows(module_fixture()))
        self.assertTrue(any("missing query/platform combinations" in e for e in errors))

    def test_planned_rows_cannot_be_marked_as_completed(self):
        rows = build_rows(module_fixture())
        rows[0]["execution_status"] = "OK"
        self.assertTrue(any("planned queue status" in e for e in validate_rows(rows)))

    def test_frozen_module_validation_rejects_prompt_mutation(self):
        expected = build_rows(module_fixture())
        actual = [dict(row) for row in expected]
        actual[0]["query"] = "Изменённый запрос"
        errors = validate_rows(actual, expected)
        self.assertTrue(any("differs from deterministic frozen-module output" in e and "query" in e for e in errors))

    def test_frozen_module_validation_rejects_all_material_field_mutations(self):
        fields = (
            "queue_id", "module_id", "module_version", "query_id", "intent",
            "country_code", "interface_locale", "prompt_language", "answer_language",
            "platform", "platform_surface", "measurement_mode", "platform_priority",
            "execution_status", "region_verification", "notes",
        )
        for field in fields:
            with self.subTest(field=field):
                expected = build_rows(module_fixture())
                actual = [dict(row) for row in expected]
                actual[0][field] = actual[0][field] + "-tampered"
                errors = validate_rows(actual, expected)
                self.assertTrue(
                    any("differs from deterministic frozen-module output" in e and field in e for e in errors),
                    msg=f"mutation of {field} was not detected: {errors}",
                )

    def test_frozen_module_validation_rejects_row_reordering(self):
        expected = build_rows(module_fixture())
        actual = list(reversed([dict(row) for row in expected]))
        errors = validate_rows(actual, expected)
        self.assertTrue(any("differs from deterministic frozen-module output" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
