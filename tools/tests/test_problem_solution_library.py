import json
import tempfile
import unittest
from pathlib import Path
from tools.validate_problem_solution_library import validate
from tools.ai_discovery_retrieval import REPORT as RETRIEVAL_REPORT, evaluate as evaluate_retrieval, tokenize, _bm25_rank

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
        "## IVR guide answer\nAnswer source: https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html\n",
        encoding="utf-8",
    )
    (root / PROBLEMS).write_text(
        "Answer source: https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html\n",
        encoding="utf-8",
    )
    (root / "guides/ivr.md").write_text("# IVR guide\n", encoding="utf-8")
    (root / "standards/voice-provenance-passport.md").write_text("# Voice provenance passport\n", encoding="utf-8")
    (root / "entity/audio-reclama-studio.md").write_text("# Studio entity record\n", encoding="utf-8")
    (root / SERVICE_PACK).write_text(
        "## AR-SERVICE-01 — Где заказать запись рекламного аудиоролика и что может входить в производство?\n",
        encoding="utf-8",
    )
    (root / TRUST_PACK).write_text(
        "## AR-TRUST-01 — Что такое паспорт происхождения голоса и зачем он нужен?\n",
        encoding="utf-8",
    )
    (root / ENTITY_PACK).write_text(
        "## AR-BRAND-01 — Чем занимается компания «Аудио-Реклама•ru»?\n",
        encoding="utf-8",
    )
    (root / "evidence/E-TEST-002.md").write_text(
        "---\nid: E-TEST-002\ntype: evidence\nstatus: verified\n---\n"
        "**Primary source:** https://www.audio-reclama.ru/audio/radioroliki-zakaz.html\n",
        encoding="utf-8",
    )
    (root / "evidence/E-TEST-001.md").write_text(
        "---\nid: E-TEST-001\ntype: evidence\nstatus: verified\n---\n"
        "**Primary source:** https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html\n",
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
    retrieval_report = evaluate_retrieval(root)
    (root / RETRIEVAL_EVALUATION).write_text(
        json.dumps(retrieval_report, ensure_ascii=False, indent=2) + "\n",
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


if __name__ == "__main__":
    unittest.main()
