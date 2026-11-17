import json
import unittest
from pathlib import Path

from tools.ai_visibility_queue import build_rows, load_module


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "research/ai-visibility-ru-brand-service-queries-2026-11-18.json"
BENCHMARK_PATH = ROOT / "research/ai-visibility-benchmark-queries-2026-11-17.json"


class RuBrandServiceQueueModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(MODULE_PATH)
        cls.benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))

    def test_module_is_separate_and_ru_scoped(self):
        self.assertEqual(self.module["schema"], "ai-visibility/query-module/1")
        self.assertEqual(self.module["market"]["country_code"], "RU")
        self.assertEqual(self.module["market"]["interface_locale"], "ru-RU")
        self.assertEqual(self.module["status"], "not_run")
        self.assertEqual(len(self.module["platform_execution_order"]), 12)

    def test_module_prompts_match_fixed_brand_service_benchmark(self):
        source = self.benchmark["queries"]
        actual = self.module["queries"]
        self.assertEqual(len(actual), 20)
        self.assertEqual(
            [(q["id"], q["query"]) for q in actual],
            [(q["id"], q["query"]) for q in source],
        )

    def test_generates_complete_240_row_planned_queue(self):
        rows = build_rows(self.module)
        self.assertEqual(len(rows), 240)
        self.assertEqual(len({row["queue_id"] for row in rows}), 240)
        self.assertEqual({row["execution_status"] for row in rows}, {"NOT_TESTED"})
        self.assertEqual({row["region_verification"] for row in rows}, {"UNVERIFIED"})
        self.assertEqual({row["country_code"] for row in rows}, {"RU"})
        self.assertEqual({row["interface_locale"] for row in rows}, {"ru-RU"})

    def test_keeps_consumer_and_search_surfaces_separate(self):
        rows = build_rows(self.module)
        modes = {row["measurement_mode"] for row in rows}
        self.assertEqual(modes, {"consumer_ui", "search_results_ui"})
        self.assertNotIn("model_api", modes)


if __name__ == "__main__":
    unittest.main()
