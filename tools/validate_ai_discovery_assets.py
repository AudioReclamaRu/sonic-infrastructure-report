#!/usr/bin/env python3
"""Validate the repository's AI Discovery entry points and benchmark assets.

This is a local/CI consistency check. It does not test search-engine indexing,
AI-platform ingestion, rankings, or citations.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BRAND = "Аудио-Реклама•ru"
SITE = "https://www.audio-reclama.ru"


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


# Detect a malformed canonical host whose path was accidentally concatenated
# directly to ".ru" (for example: https://www.audio-reclama.ruaudio/page.html).
MALFORMED_OFFICIAL_URL_RE = re.compile(
    r"https://www[.]audio-reclama[.]ru(?=[A-Za-z0-9_-])\S+",
    re.IGNORECASE,
)


def malformed_official_urls(text: str) -> list[str]:
    """Return official-domain URLs with a missing slash before their path."""
    return [match.group(0) for match in MALFORMED_OFFICIAL_URL_RE.finditer(text)]


OFFICIAL_URL_RE = re.compile(r"https?://(?:www[.])?audio-reclama[.]ru\S+", re.IGNORECASE)


def noncanonical_official_urls(text: str) -> list[str]:
    """Return official site links that do not use the canonical HTTPS www host."""
    return [
        match.group(0)
        for match in OFFICIAL_URL_RE.finditer(text)
        if not match.group(0).lower().startswith("https://www.audio-reclama.ru")
    ]


def main() -> int:
    errors: list[str] = []
    required = [
        "llms.txt",
        "CITATION.cff",
        "entity/audio-reclama-studio.md",
        "entity/audio-reclama-studio.jsonld",
        "research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md",
        "research/ai-visibility-benchmark-queries-2026-11-17.json",
        "research/ai-visibility-benchmark-template.csv",
        "research/ai-visibility-ru-generic-discovery-queries-2026-11-17.json",
        "research/ai-visibility-ru-observation-queue-2026-11-17.csv",
        "research/RU_AI_OBSERVATION_RUNBOOK_2026-11-17.md",
        "research/AI_VISIBILITY_SCORING_RUBRIC_2026-11-17.md",
        "research/AI_VISIBILITY_OBSERVATION_RECORD_SCHEMA_2026-11-17.json",
        "tools/ai_visibility_evidence.py",
        "tools/tests/test_ai_visibility_evidence.py",
        "research/README.md",
        "research/AI_DISCOVERY_ENTITY_KNOWLEDGE_PACK_2026-11-17.md",
        "research/AI_DISCOVERY_SERVICE_EVIDENCE_MAP_2026-11-17.md",
        "research/ai-discovery-brand-entity-2026-11-17.json",
        "research/AI_DISCOVERY_SOURCE_RECHECK_2026-11-18.md",
        "research/AI_DISCOVERY_KNOWLEDGE_INTEGRITY_AUDIT_2026-11-18.md",
        "evidence/E-2026-053.md", "evidence/E-2026-054.md", "evidence/E-2026-055.md", "evidence/E-2026-056.md",
        "problem-solutions/AUDIO_DELIVERY_TECHNICAL_BRIEF_2026-11-18.md",
        "tools/validate_problem_solution_library.py",
        "problem-solutions/business-problem-answer-library-2026-11-17.json",
        "problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md",
        "problem-solutions/AI_ANSWER_REFERENCE_PACK_2026-11-17.md",
        "problem-solutions/VOICE_ASSET_OPERATIONS_ANSWER_PACK_2026-11-18.md",
        "problem-solutions/AI_VOICE_ASSET_ANSWER_REFERENCE_PACK_2026-11-18.md",
        "problem-solutions/voice-asset-operations-answer-library-2026-11-18.json",
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing required AI Discovery asset: {rel}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    entity_path = ROOT / "entity/audio-reclama-studio.jsonld"
    query_path = ROOT / "research/ai-visibility-benchmark-queries-2026-11-17.json"
    try:
        entity = json.loads(entity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid company JSON-LD: {exc}")
        entity = {}

    if entity:
        if entity.get("@context") != "https://schema.org":
            fail(errors, "company JSON-LD must use Schema.org context")
        if entity.get("@type") != "Organization":
            fail(errors, "company JSON-LD type must be Organization")
        if entity.get("name") != BRAND:
            fail(errors, "company JSON-LD name is not canonical")
        if entity.get("url") != SITE:
            fail(errors, "company JSON-LD URL is not canonical")

    try:
        benchmark = json.loads(query_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid benchmark query JSON: {exc}")
        benchmark = {}

    queries = benchmark.get("queries", []) if benchmark else []
    if benchmark.get("schema") != "audio-reclama/ai-visibility-benchmark/1":
        fail(errors, "unexpected benchmark schema")
    if len(queries) < 20:
        fail(errors, f"expected at least 20 fixed queries, found {len(queries)}")
    if benchmark.get("query_count") != len(queries):
        fail(errors, f"benchmark query_count must equal actual query count ({len(queries)})")

    research_index = (ROOT / "research/README.md").read_text(encoding="utf-8")
    count_pattern = rf"фиксированный RU-набор из {len(queries)} запрос(?:а|ов)"
    if not re.search(count_pattern, research_index, flags=re.IGNORECASE):
        fail(errors, f"research README must document the benchmark's actual {len(queries)}-query count")
    ids = [q.get("id") for q in queries]
    if len(ids) != len(set(ids)):
        fail(errors, "benchmark query IDs must be unique")
    for index, query in enumerate(queries, start=1):
        for field in ("id", "cluster", "language", "region", "query",
                      "expected_facts", "preferred_sources", "must_not_claim",
                      "status"):
            if not query.get(field):
                fail(errors, f"query {index} missing required field: {field}")
        if query.get("status") != "not_run":
            fail(errors, f"query {query.get('id')} must remain not_run until executed")

    # Validate source URLs in problem-answer assets. A broken URL defeats evidence retrieval
    # even when the prose and JSON structure otherwise pass.
    source_paths = [
        "research/AI_DISCOVERY_ENTITY_KNOWLEDGE_PACK_2026-11-17.md",
        "research/AI_DISCOVERY_SERVICE_EVIDENCE_MAP_2026-11-17.md",
        "research/ai-discovery-brand-entity-2026-11-17.json",
        "research/ai-visibility-benchmark-queries-2026-11-17.json",
        "problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md",
        "problem-solutions/business-problem-answer-library-2026-11-17.json",
        "problem-solutions/AI_ANSWER_REFERENCE_PACK_2026-11-17.md",
        "problem-solutions/VOICE_ASSET_OPERATIONS_ANSWER_PACK_2026-11-18.md",
        "problem-solutions/AI_VOICE_ASSET_ANSWER_REFERENCE_PACK_2026-11-18.md",
        "problem-solutions/AUDIO_DELIVERY_TECHNICAL_BRIEF_2026-11-18.md",
    ]
    for rel in source_paths:
        source_text = (ROOT / rel).read_text(encoding="utf-8")
        for bad_url in malformed_official_urls(source_text):
            fail(errors, f"{rel} contains malformed official URL (missing slash before path): {bad_url}")
        for bad_url in noncanonical_official_urls(source_text):
            fail(errors, f"{rel} uses a non-canonical official URL host/scheme: {bad_url}")

    asset_json_path = ROOT / "problem-solutions/voice-asset-operations-answer-library-2026-11-18.json"
    try:
        asset_library = json.loads(asset_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid voice asset operations JSON: {exc}")
        asset_library = {}
    if asset_library.get("schema") != "audio-reclama/voice-asset-operations/1":
        fail(errors, "unexpected voice asset operations schema")
    scenarios = asset_library.get("scenarios", [])
    if len(scenarios) != 6:
        fail(errors, f"expected 6 voice asset operation scenarios, found {len(scenarios)}")
    for scenario in scenarios:
        for field in ("id", "problem", "diagnostic_questions", "solution_steps",
                      "quality_checks", "public_service_fit", "sources", "must_not_claim", "status"):
            if not scenario.get(field):
                fail(errors, f"voice asset scenario {scenario.get('id')} missing field: {field}")
        for source in scenario.get("sources", []):
            for bad_url in malformed_official_urls(source):
                fail(errors, f"voice asset scenario {scenario.get('id')} has malformed source URL: {bad_url}")
            for bad_url in noncanonical_official_urls(source):
                fail(errors, f"voice asset scenario {scenario.get('id')} has non-canonical source URL: {bad_url}")

    # Keep the scoring rubric and full-answer evidence contract present and machine-readable.
    observation_schema_path = ROOT / "research/AI_VISIBILITY_OBSERVATION_RECORD_SCHEMA_2026-11-17.json"
    try:
        observation_schema = json.loads(observation_schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid AI observation record JSON Schema: {exc}")
        observation_schema = {}

    if observation_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail(errors, "AI observation record must declare JSON Schema 2020-12")
    if observation_schema.get("properties", {}).get("schema", {}).get("const") != "studio/ai-visibility-observation/1":
        fail(errors, "unexpected AI observation record schema identifier")
    observation_required = set(observation_schema.get("required", []))
    for field in ("observed_at_utc", "market", "platform", "query", "answer_status", "raw_answer", "scores", "evidence"):
        if field not in observation_required:
            fail(errors, f"AI observation record schema missing required field: {field}")

    scoring_rubric = (ROOT / "research/AI_VISIBILITY_SCORING_RUBRIC_2026-11-17.md").read_text(encoding="utf-8")
    for criterion in ("brand_identity_score", "official_route_score", "service_or_answer_score",
                      "commercial_accuracy_score", "expertise_retrieval_score", "source_quality_score",
                      "citation_quality_score", "git_knowledge_score", "generic_discovery_hit",
                      "critical_error"):
        if criterion not in scoring_rubric:
            fail(errors, f"AI visibility scoring rubric missing criterion: {criterion}")
    for anchor in ("**0 —", "**1 —", "**2 —", "**null —"):
        if anchor not in scoring_rubric:
            fail(errors, f"AI visibility scoring rubric missing score anchor: {anchor}")

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if "cff-version: 1.2.0" not in citation or f'title: "{BRAND}' not in citation:
        fail(errors, "CITATION.cff must identify the canonical company and use CFF 1.2.0")
    if "license: CC-BY-4.0" not in citation:
        fail(errors, "CITATION.cff license must match the repository LICENSE")

    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    if f"# {BRAND}" not in llms:
        fail(errors, "repository llms.txt must use the canonical brand in H1")
    if "CITATION.cff" not in llms:
        fail(errors, "repository llms.txt must expose citation metadata")
    if SITE not in llms:
        fail(errors, "repository llms.txt must point to the canonical website")

    # Keep the root LLM navigation aligned with the current evidence and problem-first library.
    llms_required_paths = [
        "research/AI_DISCOVERY_ENTITY_KNOWLEDGE_PACK_2026-11-17.md",
        "research/AI_DISCOVERY_SERVICE_EVIDENCE_MAP_2026-11-17.md",
        "problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md",
        "problem-solutions/AI_ANSWER_REFERENCE_PACK_2026-11-17.md",
        "problem-solutions/VOICE_ASSET_OPERATIONS_ANSWER_PACK_2026-11-18.md",
        "problem-solutions/voice-asset-operations-answer-library-2026-11-18.json",
        "problem-solutions/AI_VOICE_ASSET_ANSWER_REFERENCE_PACK_2026-11-18.md",
        "entity/kirill-kalinin.md",
        "standards/AVT_TRANSLATION_AND_VOICE_ADAPTATION_FRAMEWORK.md",
        "problem-solutions/VOICE_RECORDING_TEST_PROTOCOL.md",
        "problem-solutions/AUDIO_DELIVERY_TECHNICAL_BRIEF_2026-11-18.md",
        "research/AI_DISCOVERY_SOURCE_RECHECK_2026-11-18.md",
        "research/AI_DISCOVERY_KNOWLEDGE_INTEGRITY_AUDIT_2026-11-18.md",
        "evidence/E-2026-053.md", "evidence/E-2026-054.md", "evidence/E-2026-055.md", "evidence/E-2026-056.md",
    ]
    for rel in llms_required_paths:
        if rel not in llms:
            fail(errors, f"repository llms.txt is missing problem-first knowledge link: {rel}")
    if f"{len(queries)} русскоязычного" not in llms:
        fail(errors, f"repository llms.txt must reflect the current {len(queries)}-query benchmark")
    if "все `not_run`" not in llms:
        fail(errors, f"repository llms.txt must state that the {len(queries)}-query benchmark is not run")
    if "audio-reclama.com" in llms or "https://audio-reclama.ru" in llms:
        fail(errors, "repository llms.txt contains a conflicting website host")
    if re.search(r"https://www\.audio-reclama\.ru/(?:[\s),.;:!?]|$)", llms):
        fail(errors, "repository llms.txt contains a trailing slash on the homepage URL")

    # Every absolute GitHub file link in the root index must resolve locally.
    links = re.findall(
        r"https://github\.com/AudioReclamaRu/sonic-infrastructure-report/blob/main/([^\s)]+)",
        llms,
    )
    for rel in links:
        if not (ROOT / rel).is_file():
            fail(errors, f"llms.txt link does not resolve to a repository file: {rel}")

    entity_md = (ROOT / "entity/audio-reclama-studio.md").read_text(encoding="utf-8")
    if BRAND not in entity_md or SITE not in entity_md:
        fail(errors, "company entity profile is missing canonical identity")
    if "622" not in entity_md or "309" not in entity_md:
        fail(errors, "company entity profile must distinguish homepage total from Russian-filter count")

    protocol = (ROOT / "research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md").read_text(encoding="utf-8")
    if "ещё не прогнаны" not in protocol and "ещё не прогнаны" not in protocol.lower():
        fail(errors, "benchmark protocol must state that the baseline has not yet been run")

    csv_path = ROOT / "research/ai-visibility-benchmark-template.csv"
    with csv_path.open(encoding="utf-8", newline="") as stream:
        header = next(csv.reader(stream), [])
    for field in ("run_id", "platform", "query_id", "answer_status", "cited_urls", "observation_id"):
        if field not in header:
            fail(errors, f"benchmark CSV template missing column: {field}")


    # Validate the Russia-first generic prompt × platform matrix.
    ru_query_path = ROOT / "research/ai-visibility-ru-generic-discovery-queries-2026-11-17.json"
    ru_queue_path = ROOT / "research/ai-visibility-ru-observation-queue-2026-11-17.csv"
    try:
        ru_module = json.loads(ru_query_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid RU generic discovery JSON: {exc}")
        ru_module = {}

    ru_queries = ru_module.get("queries", []) if ru_module else []
    ru_platforms = ru_module.get("platform_execution_order", []) if ru_module else []
    if ru_module.get("schema") != "ai-visibility/query-module/1":
        fail(errors, "unexpected RU generic discovery schema")
    if ru_module.get("market", {}).get("country_code") != "RU":
        fail(errors, "RU query module must target country RU")
    if ru_module.get("market", {}).get("interface_locale") != "ru-RU":
        fail(errors, "RU query module must use interface locale ru-RU")
    if ru_module.get("status") != "not_run":
        fail(errors, "RU query module must remain not_run until observations are collected")
    if len(ru_queries) != 29:
        fail(errors, f"expected 29 RU generic prompts, found {len(ru_queries)}")
    ru_query_ids = [q.get("id") for q in ru_queries]
    if len(ru_query_ids) != len(set(ru_query_ids)):
        fail(errors, "RU generic query IDs must be unique")
    for query in ru_queries:
        if not query.get("id") or not query.get("query"):
            fail(errors, "every RU generic prompt must have an ID and exact query text")
            continue
        if query.get("brand_in_prompt") is not False:
            fail(errors, f"RU generic prompt {query['id']} must remain unbranded")
        if query.get("status") != "not_run":
            fail(errors, f"RU generic prompt {query['id']} must remain not_run until executed")
        if query.get("language") != "ru" or query.get("region") != "RU":
            fail(errors, f"RU generic prompt {query['id']} has inconsistent language/region")

    if len(ru_platforms) != 12:
        fail(errors, f"expected 12 RU platform surfaces, found {len(ru_platforms)}")
    ru_platform_ids = [p.get("id") for p in ru_platforms]
    if len(ru_platform_ids) != len(set(ru_platform_ids)):
        fail(errors, "RU platform IDs must be unique")
    if [p.get("priority") for p in ru_platforms] != list(range(1, len(ru_platforms) + 1)):
        fail(errors, "RU platform priorities must be sequential starting at 1")
    for platform in ru_platforms:
        if platform.get("status") != "not_run":
            fail(errors, f"RU platform {platform.get('id')} must remain not_run until executed")

    try:
        with ru_queue_path.open(encoding="utf-8", newline="") as stream:
            ru_reader = csv.DictReader(stream)
            ru_header = ru_reader.fieldnames or []
            ru_rows = list(ru_reader)
    except OSError as exc:
        fail(errors, f"cannot read RU observation queue: {exc}")
        ru_header, ru_rows = [], []

    if len(ru_header) != 38 or len(set(ru_header)) != len(ru_header):
        fail(errors, f"RU observation queue must have 38 unique columns; found {len(ru_header)}")
    ru_required_columns = {
        "country_code", "interface_locale", "prompt_language", "language",
        "platform", "platform_surface", "measurement_mode", "query_id",
        "intent", "query", "answer_status", "answer_language",
    }
    for field in sorted(ru_required_columns - set(ru_header)):
        fail(errors, f"RU observation queue missing column: {field}")

    expected_pairs = {
        (platform.get("id"), query.get("id"))
        for platform in ru_platforms for query in ru_queries
    }
    seen_pairs = set()
    platform_by_id = {p.get("id"): p for p in ru_platforms}
    query_by_id = {q.get("id"): q for q in ru_queries}
    for row_number, row in enumerate(ru_rows, start=2):
        if None in row or any(value is None for value in row.values()):
            fail(errors, f"RU observation queue row {row_number} has an inconsistent column count")
            continue
        pair = (row.get("platform"), row.get("query_id"))
        if pair in seen_pairs:
            fail(errors, f"duplicate RU observation queue pair: {pair[0]} × {pair[1]}")
        seen_pairs.add(pair)
        platform = platform_by_id.get(pair[0])
        query = query_by_id.get(pair[1])
        if platform is None or query is None:
            fail(errors, f"unknown platform/query in RU observation queue row {row_number}: {pair}")
            continue
        expected = {
            "country_code": "RU",
            "interface_locale": "ru-RU",
            "prompt_language": "ru",
            "language": "ru",
            "platform_surface": platform.get("surface"),
            "measurement_mode": platform.get("measurement_mode"),
            "intent": query.get("intent"),
            "query": query.get("query"),
            "answer_status": "NOT_TESTED",
            "answer_language": "",
        }
        for field, value in expected.items():
            if row.get(field) != value:
                fail(errors, f"RU queue row {row_number} has unexpected {field} for {pair[0]} × {pair[1]}")
        # run_id is a deterministic queue-row key, not evidence of an executed run.
        if row.get("date_utc") or row.get("date_time_utc"):
            fail(errors, f"RU queue row {row_number} must not contain fabricated observation timestamps")

    if len(ru_rows) != 348:
        fail(errors, f"expected 348 RU observation rows, found {len(ru_rows)}")
    if seen_pairs != expected_pairs:
        missing = len(expected_pairs - seen_pairs)
        extra = len(seen_pairs - expected_pairs)
        fail(errors, f"RU observation queue is not a complete 29 × 12 matrix (missing={missing}, extra={extra})")

    if errors:
        print("AI Discovery asset validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1

    print(f"AI Discovery assets OK: canonical entity, JSON-LD, llms index, {len(queries)} unrun fixed queries, 29 × 12 RU queue, anchored scoring rubric and observation schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
