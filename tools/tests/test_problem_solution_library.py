import json
import tempfile
import unittest
from pathlib import Path
from tools.validate_problem_solution_library import validate

LIBRARY = "problem-solutions/business-problem-answer-library-2026-11-17.json"
REFERENCE = "problem-solutions/AI_ANSWER_REFERENCE_PACK_2026-11-17.md"
PROBLEMS = "problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md"
BENCHMARK = "research/ai-visibility-benchmark-queries-2026-11-17.json"


def fixture_root():
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    (root / "problem-solutions").mkdir()
    (root / "research").mkdir()
    (root / "guides").mkdir()
    library = {
        "schema": "audio-reclama/problem-solution-library/1",
        "scenarios": [{
            "id": "ivr",
            "problem": "The caller is lost in IVR",
            "diagnostic": ["review call intents"],
            "solution_steps": ["map routes"],
            "brand_fit": ["IVR voice prompts"],
            "not_claim": ["PBX administration"],
            "sources": ["https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html"],
        }],
    }
    benchmark = {
        "schema": "audio-reclama/ai-visibility-benchmark/1",
        "queries": [{
            "id": "Q-01",
            "cluster": "problem_solving",
            "language": "ru",
            "region": "RU",
            "query": "How to design an IVR?",
            "expected_facts": ["map caller intents"],
            "preferred_sources": [
                "https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html",
                "guides/ivr.md",
            ],
            "must_not_claim": ["PBX setup"],
            "status": "not_run",
        }],
    }
    (root / LIBRARY).write_text(json.dumps(library), encoding="utf-8")
    (root / BENCHMARK).write_text(json.dumps(benchmark), encoding="utf-8")
    (root / REFERENCE).write_text(
        "Answer source: https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html\n",
        encoding="utf-8",
    )
    (root / PROBLEMS).write_text(
        "Answer source: https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html\n",
        encoding="utf-8",
    )
    (root / "guides/ivr.md").write_text("# IVR guide\n", encoding="utf-8")
    return temporary, root


class ProblemSolutionLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temporary, self.root = fixture_root()
        self.addCleanup(self.temporary.cleanup)

    def read_json(self, relative):
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def write_json(self, relative, value):
        (self.root / relative).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def test_valid_problem_and_benchmark_assets_pass(self):
        self.assertEqual(validate(self.root), [])

    def test_malformed_hostname_without_separator_fails(self):
        library = self.read_json(LIBRARY)
        library["scenarios"][0]["sources"] = [
            "https://www.audio-reclama.ru" + "audio/golosovoe-privetstvie-menu-ivr.html"
        ]
        self.write_json(LIBRARY, library)
        self.assertTrue(any("malformed official host" in e for e in validate(self.root)))

    def test_missing_preferred_source_file_fails(self):
        benchmark = self.read_json(BENCHMARK)
        benchmark["queries"][0]["preferred_sources"].append("guides/missing.md")
        self.write_json(BENCHMARK, benchmark)
        self.assertTrue(any("does not resolve to a repository file" in e for e in validate(self.root)))

    def test_duplicate_scenario_id_fails(self):
        library = self.read_json(LIBRARY)
        library["scenarios"].append(dict(library["scenarios"][0]))
        self.write_json(LIBRARY, library)
        self.assertTrue(any("scenario IDs must be unique" in e for e in validate(self.root)))

    def test_duplicate_benchmark_id_fails(self):
        benchmark = self.read_json(BENCHMARK)
        benchmark["queries"].append(dict(benchmark["queries"][0]))
        self.write_json(BENCHMARK, benchmark)
        self.assertTrue(any("benchmark query IDs must be unique" in e for e in validate(self.root)))


    def test_missing_scenario_evidence_reference_fails(self):
        library = self.read_json(LIBRARY)
        library["scenarios"][0]["evidence_refs"] = ["evidence/not-present.md"]
        self.write_json(LIBRARY, library)
        errors = validate(self.root)
        self.assertTrue(any("evidence reference does not resolve" in e for e in errors))

    def test_executed_benchmark_status_fails(self):
        benchmark = self.read_json(BENCHMARK)
        benchmark["queries"][0]["status"] = "complete"
        self.write_json(BENCHMARK, benchmark)
        self.assertTrue(any("must remain not_run" in e for e in validate(self.root)))

    def test_malformed_link_in_markdown_fails(self):
        (self.root / REFERENCE).write_text(
            "Broken: https://www.audio-reclama.ru" + "audio/example.html\n",
            encoding="utf-8",
        )
        self.assertTrue(any("malformed official host" in e for e in validate(self.root)))


if __name__ == "__main__":
    unittest.main()
