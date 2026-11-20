import json
import tempfile
import unittest
from pathlib import Path
from tools.validate_problem_solution_library import validate
from tools.ai_discovery_retrieval import REPORT as RETRIEVAL_REPORT, evaluate as evaluate_retrieval, tokenize, _bm25_rank
from tools.ai_discovery_source_retrieval import REPORT as SOURCE_RETRIEVAL_REPORT, evaluate as evaluate_source_retrieval, validate_report as validate_source_retrieval_report
from tools.ai_discovery_answer_support import ROOT, UNIT_DISPOSITIONS, evaluate as evaluate_answer_support, extract_answer_units
from tools.ai_discovery_answer_support_review import evaluate as evaluate_answer_support_review

LIBRARY = "problem-solutions/business-problem-answer-library-2026-11-17.json"
REFERENCE = "problem-solutions/AI_ANSWER_REFERENCE_PACK_2026-11-17.md"
PROBLEMS = "problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md"
BENCHMARK = "research/ai-visibility-benchmark-queries-2026-11-17.json"
ROUTING = "problem-solutions/AI_PROBLEM_ANSWER_ROUTING_INDEX_2026-11-18.json"
SERVICE_PACK = "problem-solutions/AI_COMMERCIAL_SERVICE_ANSWER_PACK_2026-11-20.md"
SERVICE_ROUTES = "problem-solutions/AI_COMMERCIAL_SERVICE_ROUTING_2026-11-20.json"
TRUST_PACK = "problem-solutions/AI_EXPERTISE_EVIDENCE_ANSWER_PACK_2026-11-20.md"
TRUST_ROUTES = "problem-solutions/AI_EXPERTISE_EVIDENCE_ROUTING_2026-11-20.json"
ENTITY_PACK = "problem-solutions/AI_ENTITY_ANSWER_PACK_2026-11-20.md"
ENTITY_ROUTES = "problem-solutions/AI_ENTITY_ANSWER_ROUTING_2026-11-20.json"
CLAIM_SUPPORT_MATRIX = "problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json"
ANSWER_COVERAGE_AUDIT = "problem-solutions/AI_DISCOVERY_ANSWER_COVERAGE_AUDIT_2026-11-20.json"
RETRIEVAL_EVALUATION = RETRIEVAL_REPORT


def fixture_root():
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    (root / "problem-solutions").mkdir()
    (root / "research").mkdir()
    (root / "guides").mkdir()
    (root / "evidence").mkdir()
    (root / "standards").mkdir()
    (root / "entity").mkdir()
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
        }, {
            "id": "AR-SERVICE-01",
            "cluster": "commercial_service",
            "language": "ru",
            "region": "RU",
            "query": "Где заказать запись рекламного аудиоролика и что может входить в производство?",
            "expected_facts": ["radio spot production"],
            "preferred_sources": ["https://www.audio-reclama.ru/audio/radioroliki-zakaz.html", "evidence/E-TEST-002.md"],
            "must_not_claim": ["fixed price"],
            "status": "not_run",
        }, {
            "id": "AR-TRUST-01",
            "cluster": "expertise_and_evidence",
            "language": "ru",
            "region": "RU",
            "query": "Что такое паспорт происхождения голоса и зачем он нужен?",
            "expected_facts": ["origin and use boundaries"],
            "preferred_sources": ["standards/voice-provenance-passport.md"],
            "must_not_claim": ["independent certification"],
            "status": "not_run",
        }, {
            "id": "AR-BRAND-01",
            "cluster": "brand_entity",
            "language": "ru",
            "region": "RU",
            "query": "Чем занимается компания «Аудио-Реклама•ru»?",
            "expected_facts": ["studio identity"],
            "preferred_sources": ["entity/audio-reclama-studio.md"],
            "must_not_claim": ["unverified legal form"],
            "status": "not_run",
        }],
    }
    (root / LIBRARY).write_text(json.dumps(library), encoding="utf-8")
    (root / BENCHMARK).write_text(json.dumps(benchmark), encoding="utf-8")
    (root / REFERENCE).write_text(
        "## IVR guide answer\nMap caller intents before naming departments.\nAnswer source: https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html\n",
        encoding="utf-8",
    )
    (root / PROBLEMS).write_text(
        "Answer source: https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html\n",
        encoding="utf-8",
    )
    (root / "guides/ivr.md").write_text("# IVR guide\nMap caller intents before naming departments.\n", encoding="utf-8")
    (root / "standards/voice-provenance-passport.md").write_text("# Voice provenance passport\nRecords origin and use boundaries.\n", encoding="utf-8")
    (root / "entity/audio-reclama-studio.md").write_text("# Studio entity record\nThe entity record describes studio identity.\n", encoding="utf-8")
    (root / SERVICE_PACK).write_text(
        "## AR-SERVICE-01 — Где заказать запись рекламного аудиоролика и что может входить в производство?\nThe official page describes radio spot production.\n",
        encoding="utf-8",
    )
    (root / TRUST_PACK).write_text(
        "## AR-TRUST-01 — Что такое паспорт происхождения голоса и зачем он нужен?\nThe voice provenance passport records origin and use boundaries.\n",
        encoding="utf-8",
    )
    (root / ENTITY_PACK).write_text(
        "## AR-BRAND-01 — Чем занимается компания «Аудио-Реклама•ru»?\nThe studio entity record describes studio identity.\n",
        encoding="utf-8",
    )
    (root / "evidence/E-TEST-002.md").write_text(
        "---\nid: E-TEST-002\ntype: evidence\nstatus: verified\n---\n"
        "**Primary source:** https://www.audio-reclama.ru/audio/radioroliki-zakaz.html\nThe public first-party page describes radio spot production.\n",
        encoding="utf-8",
    )
    (root / "evidence/E-TEST-001.md").write_text(
        "---\nid: E-TEST-001\ntype: evidence\nstatus: verified\n---\n"
        "**Primary source:** https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html\n",
        encoding="utf-8",
    )
    (root / "evidence/E-TEST-003.md").write_text(
        "---\nid: E-TEST-003\ntype: evidence\nstatus: verified\n---\n"
        "**Primary source:** https://www.audio-reclama.ru/\n"
        "The official first-party homepage identifies the studio identity as audio production.\n",
        encoding="utf-8",
    )
    routing = {
        "schema": "audio-reclama/problem-answer-routing/1",
        "version": "1.0.0",
        "updated": "2026-11-18",
        "entry_count": 1,
        "entries": [{
            "routing_id": "business_problem/ivr",
            "intent_type": "business_problem",
            "benchmark_query_ids": ["Q-01"],
            "problem": "The caller is lost in IVR",
            "source": {"file": LIBRARY, "scenario_id": "ivr"},
            "answer_references": [
                {"file": REFERENCE, "heading": "## IVR guide answer"}
            ],
            "supporting_documents": ["guides/ivr.md"],
            "primary_sources": [
                "https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html"
            ],
            "evidence_refs": ["evidence/E-TEST-001.md"],
            "service_fit": ["IVR voice prompts"],
            "guardrails": ["PBX administration is not implied"],
        }],
    }
    (root / ROUTING).write_text(json.dumps(routing), encoding="utf-8")
    service_routes = {
        "schema": "studio/ai-commercial-service-routing/1",
        "entry_count": 1,
        "entries": [{
            "routing_id": "commercial_service/audio_advertising",
            "benchmark_query_id": "AR-SERVICE-01",
            "question": "Где заказать запись рекламного аудиоролика и что может входить в производство?",
            "answer_heading": "## AR-SERVICE-01 — Где заказать запись рекламного аудиоролика и что может входить в производство?",
            "primary_sources": ["https://www.audio-reclama.ru/audio/radioroliki-zakaz.html"],
            "evidence_refs": ["evidence/E-TEST-002.md"],
            "supporting_documents": [],
            "service_fit": ["radio ad production"],
            "guardrails": ["no fixed price"]
        }]
    }
    (root / SERVICE_ROUTES).write_text(json.dumps(service_routes), encoding="utf-8")
    expertise_routes = {
        "schema": "studio/ai-expertise-evidence-routing/1",
        "entry_count": 1,
        "entries": [{
            "routing_id": "expertise_and_evidence/voice_provenance_passport",
            "benchmark_query_id": "AR-TRUST-01",
            "question": "Что такое паспорт происхождения голоса и зачем он нужен?",
            "answer_heading": "## AR-TRUST-01 — Что такое паспорт происхождения голоса и зачем он нужен?",
            "knowledge_sources": ["guides/ivr.md"],
            "source_classes": ["internal_standard"],
            "public_source_urls": [],
            "evidence_refs": [],
            "guardrails": ["not a legal certificate"]
        }]
    }
    (root / TRUST_ROUTES).write_text(json.dumps(expertise_routes), encoding="utf-8")
    entity_routes = {
        "schema": "studio/ai-entity-answer-routing/1",
        "entry_count": 1,
        "entries": [{
            "routing_id": "brand_entity/company_identity",
            "benchmark_query_id": "AR-BRAND-01",
            "question": "Чем занимается компания «Аудио-Реклама•ru»?",
            "answer_heading": "## AR-BRAND-01 — Чем занимается компания «Аудио-Реклама•ru»?",
            "knowledge_sources": ["guides/ivr.md"],
            "source_classes": ["internal_entity_record"],
            "public_source_urls": [],
            "evidence_refs": [],
            "primary_sources": [],
            "guardrails": ["no unverified claims"]
        }]
    }
    (root / ENTITY_ROUTES).write_text(json.dumps(entity_routes), encoding="utf-8")
    claim_matrix = {
        "schema": "studio/ai-discovery-claim-support-matrix/1",
        "query_count": 4,
        "claim_count": 4,
        "semantic_review": {
            "status": "first_pass_complete",
            "reviewed_at": "2026-11-20",
            "reviewed_query_count": 4,
            "reviewed_claim_count": 4,
            "unique_source_documents": 4,
            "corrected_claim_mappings": 0,
            "method": ["Compare each expected fact to source contents."],
            "limitations": ["Internal review does not prove external AI visibility."]
        },
        "entries": [
            {
                "benchmark_query_id": "Q-01",
                "query_cluster": "problem_solving",
                "claims": [{
                    "fact_index": 1,
                    "expected_fact": "map caller intents",
                    "support_type": "internal_methodology",
                    "source_refs": ["guides/ivr.md"],
                    "scope_note": "Internal workflow recommendation, not an external client outcome.",
                    "semantic_review_status": "reviewed",
                    "semantic_review_note": "Source content checked against expected fact; scope note states limits."
                }]
            },
            {
                "benchmark_query_id": "AR-SERVICE-01",
                "query_cluster": "commercial_service",
                "claims": [{
                    "fact_index": 1,
                    "expected_fact": "radio spot production",
                    "support_type": "first_party_evidence",
                    "source_refs": ["evidence/E-TEST-002.md"],
                    "scope_note": "Evidence proves the public page wording only.",
                    "semantic_review_status": "reviewed",
                    "semantic_review_note": "Source content checked against expected fact; scope note states limits."
                }]
            },
            {
                "benchmark_query_id": "AR-TRUST-01",
                "query_cluster": "expertise_and_evidence",
                "claims": [{
                    "fact_index": 1,
                    "expected_fact": "origin and use boundaries",
                    "support_type": "internal_methodology",
                    "source_refs": ["standards/voice-provenance-passport.md"],
                    "scope_note": "Internal professional methodology, not a legal certificate.",
                    "semantic_review_status": "reviewed",
                    "semantic_review_note": "Source content checked against expected fact; scope note states limits."
                }]
            },
            {
                "benchmark_query_id": "AR-BRAND-01",
                "query_cluster": "brand_entity",
                "claims": [{
                    "fact_index": 1,
                    "expected_fact": "studio identity",
                    "support_type": "internal_methodology",
                    "source_refs": ["entity/audio-reclama-studio.md"],
                    "scope_note": "Internal entity profile; public claims need first-party evidence.",
                    "semantic_review_status": "reviewed",
                    "semantic_review_note": "Source content checked against expected fact; scope note states limits."
                }]
            }
        ]
    }
    (root / CLAIM_SUPPORT_MATRIX).write_text(json.dumps(claim_matrix), encoding="utf-8")
    answer_routes = {
        "Q-01": {"file": REFERENCE, "heading": "## IVR guide answer"},
        "AR-SERVICE-01": {"file": SERVICE_PACK, "heading": "## AR-SERVICE-01 — Где заказать запись рекламного аудиоролика и что может входить в производство?"},
        "AR-TRUST-01": {"file": TRUST_PACK, "heading": "## AR-TRUST-01 — Что такое паспорт происхождения голоса и зачем он нужен?"},
        "AR-BRAND-01": {"file": ENTITY_PACK, "heading": "## AR-BRAND-01 — Чем занимается компания «Аудио-Реклама•ru»?"},
    }
    answer_entries = []
    expected_fact_count = 0
    must_not_claim_count = 0
    for query in benchmark["queries"]:
        ref = answer_routes[query["id"]]
        answer_entries.append({
            "benchmark_query_id": query["id"],
            "query_cluster": query["cluster"],
            "query": query["query"],
            "answer_references": [ref],
            "expected_fact_checks": [
                {"fact_index": i, "expected_fact": fact, "status": "covered",
                 "review_note": "Fixture answer text checked against this expected fact."}
                for i, fact in enumerate(query["expected_facts"], start=1)
            ],
            "must_not_claim_checks": [
                {"claim_index": i, "must_not_claim": claim, "status": "not_asserted",
                 "review_note": "Fixture answer does not assert the forbidden claim."}
                for i, claim in enumerate(query["must_not_claim"], start=1)
            ],
            "overall_status": "pass",
            "reviewed_at": "2026-11-20",
            "review_method": "manual_answer_text_review",
            "review_note": "Fixture answer coverage and forbidden claims reviewed.",
        })
        expected_fact_count += len(query["expected_facts"])
        must_not_claim_count += len(query["must_not_claim"])
    answer_audit = {
        "schema": "studio/ai-discovery-answer-coverage-audit/1",
        "query_count": len(answer_entries),
        "expected_fact_count": expected_fact_count,
        "must_not_claim_count": must_not_claim_count,
        "entries": answer_entries,
    }
    (root / ANSWER_COVERAGE_AUDIT).write_text(json.dumps(answer_audit), encoding="utf-8")
    (root / UNIT_DISPOSITIONS).write_text(json.dumps({
        "schema": "studio/ai-discovery-answer-unit-dispositions/1",
        "updated": "2026-11-20",
        "disposition_count": 0,
        "dispositions": [],
    }), encoding="utf-8")
    retrieval_report = evaluate_retrieval(root)
    (root / RETRIEVAL_EVALUATION).write_text(
        json.dumps(retrieval_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    source_report = evaluate_source_retrieval(root)
    source_baseline = {
        key: source_report[key]
        for key in ("schema", "date", "status", "method", "corpus", "metrics", "source_class_aware")
    }
    source_baseline["baseline_review_status"] = "reviewed"
    (root / SOURCE_RETRIEVAL_REPORT).write_text(
        json.dumps(source_baseline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
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


    def test_claim_support_matrix_must_cover_every_benchmark_prompt(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        matrix["entries"] = matrix["entries"][:-1]
        matrix["query_count"] = 3
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        errors = validate(self.root)
        self.assertTrue(any("exactly one entry per benchmark query" in e for e in errors))

    def test_claim_support_fact_must_match_exact_expected_fact(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        matrix["entries"][0]["claims"][0]["expected_fact"] = "different fact"
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        errors = validate(self.root)
        self.assertTrue(any("does not exactly match benchmark expected_facts" in e for e in errors))

    def test_claim_support_source_must_resolve_and_be_preferred(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        matrix["entries"][0]["claims"][0]["source_refs"] = ["guides/missing.md"]
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        errors = validate(self.root)
        self.assertTrue(any("does not resolve to a safe repository file" in e for e in errors))

    def test_claim_support_type_must_match_referenced_files(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        matrix["entries"][0]["claims"][0]["support_type"] = "first_party_evidence"
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        errors = validate(self.root)
        self.assertTrue(any("does not match referenced source classes" in e for e in errors))

    def test_claim_support_requires_semantic_review_status(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        matrix["entries"][0]["claims"][0]["semantic_review_status"] = "pending"
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        errors = validate(self.root)
        self.assertTrue(any("must be marked reviewed" in e for e in errors))


    def test_answer_support_candidate_evaluation_tracks_required_source_classes(self):
        result = evaluate_answer_support(self.root)
        metrics = result["metrics"]
        self.assertEqual(metrics["query_count"], 4)
        self.assertEqual(metrics["answer_unit_count"], 4)
        self.assertEqual(metrics["units_with_expected_fact_candidate"], 4)
        self.assertEqual(metrics["units_without_expected_fact_candidate"], 0)
        units = {unit["benchmark_query_id"]: unit for unit in result["units"]}
        self.assertEqual(
            units["Q-01"]["required_source_classes"],
            ["internal_methodology"],
        )
        self.assertEqual(
            units["AR-SERVICE-01"]["required_source_classes"],
            ["first_party_evidence"],
        )
        self.assertTrue(units["Q-01"]["all_required_classes_top_3"])
        self.assertTrue(units["AR-SERVICE-01"]["all_required_classes_top_3"])
        self.assertEqual(result["status"], "candidate_retrieval_only")

    def test_dispositions_use_the_narrowest_semantically_relevant_source_class(self):
        asset = json.loads((ROOT / UNIT_DISPOSITIONS).read_text(encoding="utf-8"))
        by_id = {item["unit_id"]: item for item in asset["dispositions"]}

        # Public page limitations should not inherit an unrelated internal release standard.
        for unit_id in ("AR-BRAND-01::06", "AR-BRAND-02::06", "AR-SERVICE-13::03", "AR-SERVICE-13::04"):
            self.assertEqual(by_id[unit_id]["required_source_classes"], ["first_party_evidence"])
        self.assertNotIn("standards/responsible-release.md", by_id["AR-BRAND-01::06"]["source_refs"])
        self.assertNotIn("standards/responsible-release.md", by_id["AR-SERVICE-13::04"]["source_refs"])

        # Chronomer snapshot caveats are supported by the dated first-party snapshot itself.
        for unit_id in ("AR-PROBLEM-04::05", "AR-PROBLEM-06::04", "AR-PROBLEM-06::05"):
            self.assertEqual(by_id[unit_id]["source_refs"], ["evidence/E-2026-111.md"])

        # The price instruction is internal commercial guidance, not a public page fact.
        price = by_id["AR-SERVICE-06::05"]
        self.assertEqual(price["category"], "internal_recommendation")
        self.assertEqual(price["required_source_classes"], ["internal_methodology"])
        self.assertEqual(price["source_refs"], ["entity/audio-reclama-studio.md"])

        # Music and corporate-song rights guidance must use the dedicated problem methodology.
        for unit_id in ("AR-SERVICE-05::04", "AR-PROBLEM-22::03", "AR-PROBLEM-23::04"):
            self.assertEqual(
                by_id[unit_id]["source_refs"],
                ["problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md"]
            )

        # AI training/cloning caution uses the explicit internal policy plus dated public snapshots.
        ai_scope = by_id["AR-TRUST-03::14"]
        self.assertEqual(
            ai_scope["source_refs"],
            [
                "evidence/E-2026-098.md",
                "evidence/E-2026-104.md",
                "evidence/E-2026-110.md",
                "problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md"
            ]
        )

    def test_low_rank_inventory_uses_distinct_denominators_and_source_text(self):
        report = evaluate_answer_support_review()
        metrics = report["metrics"]
        self.assertEqual(metrics["manual_disposition_unit_count"], 285)
        self.assertEqual(metrics["retrieval_required_unit_count"], 275)
        self.assertEqual(metrics["no_retrieval_unit_count"], 10)
        self.assertEqual(metrics["units_with_expected_fact_candidate"], 236)
        self.assertEqual(metrics["candidate_units_all_required_classes_top_3"], 176)
        self.assertEqual(metrics["candidate_units_all_required_classes_top_5"], 201)
        self.assertEqual(metrics["candidate_units_all_required_classes_top_10"], 221)
        self.assertEqual(metrics["low_rank_unit_count"], 38)
        self.assertEqual(metrics["retrieval_units_with_mapped_sources_top_5"], 237)
        self.assertEqual(len(report["units"]), 38)
        for unit in report["units"]:
            compact = {
                "id": unit["unit_id"],
                "query": unit["benchmark_query_id"],
                "category": unit["category"],
                "text": unit["answer_text"],
                "ranks": unit["best_mapped_source_rank_by_class"],
                "sources": [
                    {
                        "path": source["path"],
                        "rank": source["lexical_rank"],
                        "metadata": source["metadata"],
                        "excerpts": [
                            excerpt["text"][:850]
                            for excerpt in source["text_excerpt_candidates"][:1]
                        ],
                    }
                    for review in unit["source_reviews"]
                    for source in review["mapped_sources"]
                ],
                "top_5_candidates_by_class": [
                    {
                        "source_class": review["source_class"],
                        "candidates": review["top_5_candidates"]
                    }
                    for review in unit["source_reviews"]
                ],
            }
            print("LOW_RANK_SOURCE_TEXT_REVIEW " + json.dumps(compact, ensure_ascii=False, sort_keys=True))
        for unit in report["units"]:
            self.assertEqual(unit["semantic_verdict"], "pending_manual_source_text_review")
            self.assertTrue(unit["source_reviews"])
            for source_review in unit["source_reviews"]:
                self.assertTrue(source_review["mapped_sources"])
                for mapped_source in source_review["mapped_sources"]:
                    self.assertIn("lexical_rank", mapped_source)
                    self.assertTrue(mapped_source["text_excerpt_candidates"])
                    self.assertIn("metadata", mapped_source)

    def test_answer_support_mixed_claim_requires_both_source_classes(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        brand_entry = next(
            entry for entry in matrix["entries"]
            if entry["benchmark_query_id"] == "AR-BRAND-01"
        )
        claim = brand_entry["claims"][0]
        claim["support_type"] = "mixed"
        claim["source_refs"] = [
            "evidence/E-TEST-003.md",
            "entity/audio-reclama-studio.md",
        ]
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        unit = next(
            item for item in evaluate_answer_support(self.root)["units"]
            if item["benchmark_query_id"] == "AR-BRAND-01"
        )
        self.assertEqual(
            unit["required_source_classes"],
            ["first_party_evidence", "internal_methodology"],
        )
        self.assertTrue(unit["all_required_classes_top_3"])
        self.assertTrue(unit["source_candidates_by_class"]["first_party_evidence"][0]["is_mapped_source"])
        self.assertTrue(unit["source_candidates_by_class"]["internal_methodology"][0]["is_mapped_source"])

    def test_answer_support_rejects_mismatched_claim_source_classes(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        matrix["entries"][0]["claims"][0]["source_refs"] = [
            "guides/ivr.md",
            "evidence/E-TEST-001.md",
        ]
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        with self.assertRaisesRegex(ValueError, "source classes"):
            evaluate_answer_support(self.root)

    def test_answer_support_marks_unmatched_sentence_for_human_review(self):
        answer_file = self.root / SERVICE_PACK
        answer_file.write_text(
            answer_file.read_text(encoding="utf-8")
            + "Every campaign guarantees a sales increase.\n",
            encoding="utf-8",
        )
        result = evaluate_answer_support(self.root)
        unmatched = result["unmatched_units"]
        self.assertEqual(len(unmatched), 1)
        self.assertEqual(unmatched[0]["benchmark_query_id"], "AR-SERVICE-01")
        self.assertIn("guarantees a sales increase", unmatched[0]["answer_text"])
        self.assertTrue(unmatched[0]["manual_review_required"])

    def test_answer_support_uses_unit_disposition_instead_of_whole_fact_classes(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        service = next(
            entry for entry in matrix["entries"]
            if entry["benchmark_query_id"] == "AR-SERVICE-01"
        )
        service["claims"][0]["support_type"] = "mixed"
        service["claims"][0]["source_refs"] = [
            "evidence/E-TEST-002.md",
            "guides/ivr.md",
        ]
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)

        baseline = evaluate_answer_support(self.root)
        unit = next(
            item for item in baseline["units"]
            if item["unit_id"] == "AR-SERVICE-01::01"
        )
        self.assertEqual(
            unit["required_source_classes"],
            ["first_party_evidence", "internal_methodology"],
        )

        dispositions = self.read_json(UNIT_DISPOSITIONS)
        dispositions["disposition_count"] = 1
        dispositions["dispositions"] = [{
            "unit_id": unit["unit_id"],
            "benchmark_query_id": unit["benchmark_query_id"],
            "answer_file": unit["answer_file"],
            "answer_heading": unit["answer_heading"],
            "answer_text": unit["answer_text"],
            "category": "first_party_fact",
            "required_source_classes": ["first_party_evidence"],
            "source_refs": ["evidence/E-TEST-002.md"],
            "review_status": "manual_reviewed",
            "review_date": "2026-11-20",
            "review_note": "This exact sentence states a public service fact.",
        }]
        self.write_json(UNIT_DISPOSITIONS, dispositions)

        result = evaluate_answer_support(self.root)
        unit = next(
            item for item in result["units"]
            if item["unit_id"] == "AR-SERVICE-01::01"
        )
        self.assertEqual(
            unit["candidate_fact_required_source_classes"],
            ["first_party_evidence", "internal_methodology"],
        )
        self.assertEqual(unit["required_source_classes"], ["first_party_evidence"])
        self.assertEqual(unit["unit_disposition"]["category"], "first_party_fact")
        self.assertFalse(unit["manual_review_required"])
        self.assertEqual(result["metrics"]["manual_disposition_unit_count"], 1)

    def test_answer_support_general_legal_caution_does_not_force_a_source_channel(self):
        trust_file = self.root / TRUST_PACK
        trust_file.write_text(
            trust_file.read_text(encoding="utf-8")
            + "Any project-specific legal conclusion requires separate advice.\n",
            encoding="utf-8",
        )
        result = evaluate_answer_support(self.root)
        unit = next(
            item for item in result["units"]
            if item["unit_id"] == "AR-TRUST-01::02"
        )
        dispositions = self.read_json(UNIT_DISPOSITIONS)
        dispositions["disposition_count"] = 1
        dispositions["dispositions"] = [{
            "unit_id": unit["unit_id"],
            "benchmark_query_id": unit["benchmark_query_id"],
            "answer_file": unit["answer_file"],
            "answer_heading": unit["answer_heading"],
            "answer_text": unit["answer_text"],
            "category": "general_legal_caution",
            "required_source_classes": [],
            "source_refs": [],
            "review_status": "manual_reviewed",
            "review_date": "2026-11-20",
            "review_note": "Generic caution only; it makes no company-specific factual claim.",
        }]
        self.write_json(UNIT_DISPOSITIONS, dispositions)
        result = evaluate_answer_support(self.root)
        unit = next(
            item for item in result["units"]
            if item["unit_id"] == "AR-TRUST-01::02"
        )
        self.assertFalse(unit["retrieval_required"])
        self.assertEqual(unit["required_source_classes"], [])
        self.assertIsNone(unit["all_required_classes_top_5"])
        self.assertFalse(unit["manual_review_required"])

    def test_answer_support_rejects_stale_unit_disposition_text(self):
        result = evaluate_answer_support(self.root)
        unit = next(
            item for item in result["units"]
            if item["unit_id"] == "AR-SERVICE-01::01"
        )
        dispositions = self.read_json(UNIT_DISPOSITIONS)
        dispositions["disposition_count"] = 1
        dispositions["dispositions"] = [{
            "unit_id": unit["unit_id"],
            "benchmark_query_id": unit["benchmark_query_id"],
            "answer_file": unit["answer_file"],
            "answer_heading": unit["answer_heading"],
            "answer_text": "This text was not in the answer pack.",
            "category": "first_party_fact",
            "required_source_classes": ["first_party_evidence"],
            "source_refs": ["evidence/E-TEST-002.md"],
            "review_status": "manual_reviewed",
            "review_date": "2026-11-20",
            "review_note": "Test stale disposition protection.",
        }]
        self.write_json(UNIT_DISPOSITIONS, dispositions)
        with self.assertRaisesRegex(ValueError, "text drift"):
            evaluate_answer_support(self.root)

    def test_answer_support_rejects_incomplete_declared_unit_disposition_coverage(self):
        result = evaluate_answer_support(self.root)
        dispositions = self.read_json(UNIT_DISPOSITIONS)
        dispositions["coverage_status"] = "all_extracted_answer_units_dispositioned"
        dispositions["dispositioned_all_answer_units"] = result["metrics"]["answer_unit_count"]
        dispositions["disposition_count"] = 0
        dispositions["dispositions"] = []
        self.write_json(UNIT_DISPOSITIONS, dispositions)
        with self.assertRaisesRegex(ValueError, "complete answer-unit disposition coverage has missing units"):
            evaluate_answer_support(self.root)

    def test_answer_unit_extraction_ignores_source_footers_and_splits_sentences(self):
        extracted = extract_answer_units(
            "## Heading\nOne factual sentence. A second clause; a third clause.\n"
            "Источник: https://example.org/page\n"
            "Публичные страницы: https://example.org/a ; evidence/E-001.md\n"
            "Публичная услуга: https://example.org/b ; внутренняя методика: guide.md\n"
            "## Next\nIgnored.",
            "## Heading",
        )
        self.assertEqual(
            extracted,
            ["One factual sentence.", "A second clause;", "a third clause."],
        )


    def test_answer_coverage_must_include_every_expected_fact(self):
        audit = self.read_json(ANSWER_COVERAGE_AUDIT)
        audit["entries"][0]["expected_fact_checks"] = []
        self.write_json(ANSWER_COVERAGE_AUDIT, audit)
        errors = validate(self.root)
        self.assertTrue(any("must check every expected fact" in e for e in errors))

    def test_answer_coverage_heading_must_resolve(self):
        audit = self.read_json(ANSWER_COVERAGE_AUDIT)
        audit["entries"][0]["answer_references"][0]["heading"] = "## Missing answer heading"
        self.write_json(ANSWER_COVERAGE_AUDIT, audit)
        errors = validate(self.root)
        self.assertTrue(any("heading does not resolve" in e for e in errors))

    def test_answer_coverage_must_review_every_forbidden_claim(self):
        audit = self.read_json(ANSWER_COVERAGE_AUDIT)
        audit["entries"][0]["must_not_claim_checks"] = []
        self.write_json(ANSWER_COVERAGE_AUDIT, audit)
        errors = validate(self.root)
        self.assertTrue(any("must check every must_not_claim" in e for e in errors))

    def test_answer_coverage_rejects_unreviewed_forbidden_claim(self):
        audit = self.read_json(ANSWER_COVERAGE_AUDIT)
        audit["entries"][0]["must_not_claim_checks"][0]["status"] = "unchecked"
        self.write_json(ANSWER_COVERAGE_AUDIT, audit)
        errors = validate(self.root)
        self.assertTrue(any("must be marked not_asserted or explicitly_guarded" in e for e in errors))


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

    def test_commercial_service_query_must_have_a_route(self):
        routes = self.read_json(SERVICE_ROUTES)
        routes["entries"] = []
        routes["entry_count"] = 0
        self.write_json(SERVICE_ROUTES, routes)
        errors = validate(self.root)
        self.assertTrue(any("commercial-service benchmark query is not mapped" in e for e in errors))

    def test_commercial_service_primary_source_must_be_bound_to_evidence(self):
        routes = self.read_json(SERVICE_ROUTES)
        routes["entries"][0]["primary_sources"] = [
            "https://www.audio-reclama.ru/audio/ozvuchka-video.html"
        ]
        self.write_json(SERVICE_ROUTES, routes)
        errors = validate(self.root)
        self.assertTrue(any("is not covered by any linked evidence_refs record" in e for e in errors))

    def test_commercial_service_heading_must_resolve(self):
        routes = self.read_json(SERVICE_ROUTES)
        routes["entries"][0]["answer_heading"] = "## Missing commercial answer"
        self.write_json(SERVICE_ROUTES, routes)
        errors = validate(self.root)
        self.assertTrue(any("answer heading does not resolve" in e for e in errors))

    def test_expertise_evidence_query_must_have_route(self):
        routes = self.read_json(TRUST_ROUTES)
        routes["entries"] = []
        routes["entry_count"] = 0
        self.write_json(TRUST_ROUTES, routes)
        errors = validate(self.root)
        self.assertTrue(any("expertise/evidence benchmark query is not mapped" in e for e in errors))

    def test_expertise_knowledge_source_must_resolve(self):
        routes = self.read_json(TRUST_ROUTES)
        routes["entries"][0]["knowledge_sources"] = ["standards/missing.md"]
        self.write_json(TRUST_ROUTES, routes)
        errors = validate(self.root)
        self.assertTrue(any("knowledge_sources[1] does not resolve" in e for e in errors))

    def test_brand_entity_query_must_have_route(self):
        routes = self.read_json(ENTITY_ROUTES)
        routes["entries"] = []
        routes["entry_count"] = 0
        self.write_json(ENTITY_ROUTES, routes)
        errors = validate(self.root)
        self.assertTrue(any("brand/entity benchmark query is not mapped" in e for e in errors))

    def test_brand_entity_knowledge_source_must_resolve(self):
        routes = self.read_json(ENTITY_ROUTES)
        routes["entries"][0]["knowledge_sources"] = ["entity/missing.md"]
        self.write_json(ENTITY_ROUTES, routes)
        errors = validate(self.root)
        self.assertTrue(any("knowledge_sources[1] does not resolve" in e for e in errors))

    def test_executed_benchmark_status_fails(self):
        benchmark = self.read_json(BENCHMARK)
        benchmark["queries"][0]["status"] = "complete"
        self.write_json(BENCHMARK, benchmark)
        self.assertTrue(any("must remain not_run" in e for e in validate(self.root)))

    def test_routing_index_missing_answer_heading_fails(self):
        routing = self.read_json(ROUTING)
        routing["entries"][0]["answer_references"][0]["heading"] = "## Missing heading"
        self.write_json(ROUTING, routing)
        errors = validate(self.root)
        self.assertTrue(any("heading does not resolve" in e for e in errors))

    def test_routing_entry_without_evidence_refs_fails(self):
        routing = self.read_json(ROUTING)
        routing["entries"][0]["evidence_refs"] = []
        self.write_json(ROUTING, routing)
        errors = validate(self.root)
        self.assertTrue(any("missing required field: evidence_refs" in e for e in errors))

    def test_routing_primary_source_must_be_bound_to_evidence_record(self):
        routing = self.read_json(ROUTING)
        routing["entries"][0]["primary_sources"] = [
            "https://www.audio-reclama.ru/audio/ozvuchka-video.html"
        ]
        self.write_json(ROUTING, routing)
        errors = validate(self.root)
        self.assertTrue(any("is not covered by any linked evidence_refs record" in e for e in errors))

    def test_primary_source_cannot_be_an_internal_repository_file(self):
        routing = self.read_json(ROUTING)
        routing["entries"][0]["primary_sources"] = ["guides/ivr.md"]
        self.write_json(ROUTING, routing)
        errors = validate(self.root)
        self.assertTrue(any("must be an absolute HTTPS URL" in e for e in errors))

    def test_evidence_record_must_identify_its_primary_source(self):
        evidence_path = self.root / "evidence/E-TEST-001.md"
        evidence_path.write_text(
            "---\nid: E-TEST-001\ntype: evidence\nstatus: verified\n---\n"
            "This record has no primary source field.\n",
            encoding="utf-8",
        )
        errors = validate(self.root)
        self.assertTrue(any("has no explicit Primary source URL" in e for e in errors))

    def test_evidence_record_accepts_plural_primary_source_list(self):
        evidence_path = self.root / "evidence/E-TEST-001.md"
        evidence_path.write_text(
            "---\nid: E-TEST-001\ntype: evidence\nstatus: verified\n---\n"
            "**Primary sources:**\n"
            "- https://www.audio-reclama.ru\n"
            "- https://www.audio-reclama.ru/diktoryi/\n",
            encoding="utf-8",
        )
        errors = validate(self.root)
        self.assertFalse(any("has no explicit HTTPS Primary source URL" in e for e in errors))

    def test_routing_index_unknown_benchmark_query_fails(self):
        routing = self.read_json(ROUTING)
        routing["entries"][0]["benchmark_query_ids"] = ["Q-UNKNOWN"]
        self.write_json(ROUTING, routing)
        errors = validate(self.root)
        self.assertTrue(any("unknown benchmark query" in e for e in errors))

    def test_routing_index_missing_source_scenario_fails(self):
        routing = self.read_json(ROUTING)
        routing["entries"][0]["source"]["scenario_id"] = "missing"
        self.write_json(ROUTING, routing)
        errors = validate(self.root)
        self.assertTrue(any("does not resolve scenario" in e for e in errors))

    def test_malformed_link_in_markdown_fails(self):
        (self.root / REFERENCE).write_text(
            "Broken: https://www.audio-reclama.ru" + "audio/example.html\n",
            encoding="utf-8",
        )
        self.assertTrue(any("malformed official host" in e for e in validate(self.root)))


    def test_retrieval_tokenizer_normalizes_russian_inflections(self):
        terms = tokenize("Дикторов и дикторами проверяют произношение")
        self.assertGreaterEqual(terms.count("диктор"), 2)

    def test_bm25_prefers_the_section_matching_the_query(self):
        documents = [
            {"file": "a.md", "heading": "Pronunciation brief", "text": "pronunciation names numbers announcer voice message"},
            {"file": "b.md", "heading": "Airport announcements", "text": "airport multilingual announcements passenger route"},
        ]
        document_tokens = [tokenize(item["text"]) for item in documents]
        document_frequency = {}
        for terms in document_tokens:
            for term in set(terms):
                document_frequency[term] = document_frequency.get(term, 0) + 1
        average_length = sum(map(len, document_tokens)) / len(document_tokens)
        ranked = _bm25_rank(
            "How to check pronunciation of names and numbers in a voice message",
            documents,
            document_tokens,
            document_frequency,
            average_length,
        )
        self.assertEqual(ranked[0]["heading"], "Pronunciation brief")

    def test_retrieval_report_matches_current_answer_corpus(self):
        errors = validate(self.root)
        self.assertFalse(any("retrieval evaluation is stale" in error for error in errors), errors)

    def test_retrieval_report_stale_metrics_fail(self):
        report = self.read_json(RETRIEVAL_EVALUATION)
        report["metrics"]["primary_top_3"] = 0
        self.write_json(RETRIEVAL_EVALUATION, report)
        errors = validate(self.root)
        self.assertTrue(any("retrieval evaluation is stale or inconsistent" in error for error in errors))


    def test_claim_source_retrieval_corpus_matches_claim_matrix(self):
        report = evaluate_source_retrieval(self.root)
        self.assertEqual(report["metrics"]["mapped_source_documents"], 4)
        self.assertEqual(report["metrics"]["expected_fact_count"], 4)
        self.assertEqual(report["metrics"]["claims_with_mapped_source_top_10"], 4)

    def test_claim_source_retrieval_separates_first_party_evidence(self):
        report = evaluate_source_retrieval(self.root)
        metrics = report["metrics"]
        self.assertGreaterEqual(metrics["claims_with_first_party_evidence"], 1)
        self.assertLessEqual(
            metrics["evidence_claims_with_evidence_top_5"],
            metrics["claims_with_first_party_evidence"],
        )
        routed = report["source_class_aware"]
        self.assertEqual(routed["source_class_document_counts"], {
            "first_party_evidence": 1,
            "internal_methodology": 3,
        })
        self.assertEqual(routed["query_route_counts"]["first_party_evidence_only"], 1)
        self.assertEqual(routed["query_route_counts"]["internal_methodology_only"], 3)
        self.assertEqual(routed["claim_support_type_counts"], {
            "internal_methodology": 3,
            "first_party_evidence": 1,
        })

    def test_mixed_claim_uses_parallel_evidence_and_methodology_channels(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        claim = matrix["entries"][0]["claims"][0]
        claim["support_type"] = "mixed"
        claim["source_refs"] = ["guides/ivr.md", "evidence/E-TEST-001.md"]
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        report = evaluate_source_retrieval(self.root)
        entry = report["entries"][0]
        routed_claim = entry["claims"][0]
        self.assertEqual(entry["query_source_class_route"], "parallel")
        self.assertEqual(
            set(routed_claim["class_aware_source_ranks"]),
            {"first_party_evidence", "internal_methodology"},
        )
        self.assertEqual(
            routed_claim["required_source_classes"],
            ["first_party_evidence", "internal_methodology"],
        )
        self.assertEqual(report["source_class_aware"]["mixed_claim_count"], 1)

    def test_claim_support_type_rejects_mismatched_source_classes(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        matrix["entries"][0]["claims"][0]["source_refs"] = [
            "guides/ivr.md", "evidence/E-TEST-001.md"
        ]
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        with self.assertRaisesRegex(ValueError, "but support_type 'internal_methodology' requires"):
            evaluate_source_retrieval(self.root)

    def test_claim_source_retrieval_fails_on_missing_mapped_source(self):
        matrix = self.read_json(CLAIM_SUPPORT_MATRIX)
        matrix["entries"][0]["claims"][0]["source_refs"] = ["guides/missing.md"]
        self.write_json(CLAIM_SUPPORT_MATRIX, matrix)
        with self.assertRaisesRegex(ValueError, "cannot read mapped source"):
            evaluate_source_retrieval(self.root)

    def test_claim_source_retrieval_baseline_matches_current_corpus(self):
        self.assertEqual(validate_source_retrieval_report(self.root), [])

    def test_claim_source_retrieval_baseline_rejects_unreviewed_or_stale_metrics(self):
        report = self.read_json(SOURCE_RETRIEVAL_REPORT)
        report["baseline_review_status"] = "pending"
        report["metrics"]["claims_with_mapped_source_top_3"] = 0
        self.write_json(SOURCE_RETRIEVAL_REPORT, report)
        errors = validate_source_retrieval_report(self.root)
        self.assertTrue(any("baseline is stale or inconsistent: metrics" in e for e in errors))
        self.assertTrue(any("must be marked reviewed" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
