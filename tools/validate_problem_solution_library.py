#!/usr/bin/env python3
"""Validate problem-solution knowledge, source URLs and benchmark references."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = "problem-solutions/business-problem-answer-library-2026-11-17.json"
REFERENCE_PACK = "problem-solutions/AI_ANSWER_REFERENCE_PACK_2026-11-17.md"
PROBLEM_LIBRARY = "problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md"
BENCHMARK = "research/ai-visibility-benchmark-queries-2026-11-17.json"
VOICE_ASSET_LIBRARY = "problem-solutions/voice-asset-operations-answer-library-2026-11-18.json"
ROUTING_INDEX = "problem-solutions/AI_PROBLEM_ANSWER_ROUTING_INDEX_2026-11-18.json"
ROUTING_SCHEMA = "audio" + "-reclama/problem-answer-routing/1"
OFFICIAL_DOMAIN = "audio-" + "reclama" + ".ru"
CANONICAL_HOST = "www." + OFFICIAL_DOMAIN
LIBRARY_SCHEMA = "audio" + "-reclama/problem-solution-library/1"
BENCHMARK_SCHEMA = "audio" + "-reclama/ai-visibility-benchmark/1"
URL_PATTERN = re.compile(r"https?://[^\s<>\]]+")


def _read_json(path: Path, errors: list[str], label: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing required file: {label}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {label}: {exc}")
    except OSError as exc:
        errors.append(f"cannot read {label}: {exc}")
    return None


def _clean_url(raw: str) -> str:
    return raw.rstrip(".,;:!?)]}’\"")


def _validate_url(raw: str, label: str, errors: list[str]) -> None:
    value = _clean_url(raw)
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
    except ValueError as exc:
        errors.append(f"{label}: malformed URL {raw!r}: {exc}")
        return
    if parsed.scheme != "https" or not host:
        errors.append(f"{label}: source must be an absolute HTTPS URL: {raw}")
        return
    if OFFICIAL_DOMAIN in host and host != CANONICAL_HOST:
        errors.append(f"{label}: non-canonical or malformed official host {host!r}: {raw}")


def _urls_in_text(content: str):
    for match in URL_PATTERN.finditer(content):
        yield match.start(), _clean_url(match.group(0))


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    library = _read_json(root / LIBRARY, errors, LIBRARY) or {}
    scenarios = library.get("scenarios", [])
    if library.get("schema") != LIBRARY_SCHEMA:
        errors.append("unexpected business problem library schema")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("business problem library must contain at least one scenario")
        scenarios = []

    scenario_ids: list[str] = []
    required_scenario_fields = ("id", "problem", "diagnostic", "solution_steps", "brand_fit", "not_claim", "sources")
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            errors.append(f"scenario {index} must be an object")
            continue
        for field in required_scenario_fields:
            if field not in scenario or scenario[field] in (None, "", []):
                errors.append(f"scenario {index} missing required field: {field}")
        sid = scenario.get("id")
        if isinstance(sid, str) and sid:
            scenario_ids.append(sid)
        for field in ("diagnostic", "solution_steps", "brand_fit", "not_claim", "sources"):
            value = scenario.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"scenario {sid or index} field {field} must be a non-empty list")
        sources = scenario.get("sources")
        for source_index, source in enumerate(sources if isinstance(sources, list) else [], start=1):
            if not isinstance(source, str):
                errors.append(f"scenario {sid or index} source {source_index} must be a URL string")
            else:
                _validate_url(source, f"scenario {sid or index} source {source_index}", errors)

        evidence_refs = scenario.get("evidence_refs", [])
        if evidence_refs and not isinstance(evidence_refs, list):
            errors.append(f"scenario {sid or index} evidence_refs must be a list of repository paths")
        for evidence_index, evidence_ref in enumerate(evidence_refs if isinstance(evidence_refs, list) else [], start=1):
            if not isinstance(evidence_ref, str) or evidence_ref.startswith("/") or ".." in Path(evidence_ref).parts:
                errors.append(f"scenario {sid or index} evidence reference {evidence_index} must be a safe repository-relative path")
            elif not (root / evidence_ref).is_file():
                errors.append(f"scenario {sid or index} evidence reference does not resolve: {evidence_ref}")
    if len(scenario_ids) != len(set(scenario_ids)):
        errors.append("business problem scenario IDs must be unique")

    # Verify the routing graph end to end: source scenario -> exact answer
    # heading -> supporting documents -> primary sources and evidence files.
    routing = _read_json(root / ROUTING_INDEX, errors, ROUTING_INDEX) or {}
    if routing.get("schema") != ROUTING_SCHEMA:
        errors.append("unexpected problem-answer routing index schema")
    entries = routing.get("entries", [])
    if not isinstance(entries, list) or not entries:
        errors.append("problem-answer routing index must contain entries")
        entries = []
    if routing.get("entry_count") != len(entries):
        errors.append("problem-answer routing index entry_count must equal actual entries")

    routing_ids: list[str] = []
    routing_benchmark_query_ids: list[str] = []
    source_cache: dict[str, dict] = {}
    markdown_cache: dict[str, str] = {}
    required_route_fields = (
        "routing_id", "intent_type", "problem", "source", "answer_references",
        "supporting_documents", "primary_sources", "benchmark_query_ids",
        "service_fit", "guardrails",
    )

    def safe_relative_path(value: object) -> bool:
        return (
            isinstance(value, str)
            and bool(value)
            and not value.startswith("/")
            and ".." not in Path(value).parts
        )

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"routing entry {index} must be an object")
            continue
        for field in required_route_fields:
            if field not in entry or entry[field] in (None, "", []):
                errors.append(f"routing entry {index} missing required field: {field}")

        routing_id = entry.get("routing_id")
        if isinstance(routing_id, str) and routing_id:
            routing_ids.append(routing_id)

        benchmark_refs = entry.get("benchmark_query_ids")
        if not isinstance(benchmark_refs, list) or not benchmark_refs:
            errors.append(f"routing entry {routing_id or index} must have benchmark_query_ids")
            benchmark_refs = []
        if any(not isinstance(query_id, str) or not query_id for query_id in benchmark_refs):
            errors.append(f"routing entry {routing_id or index} benchmark_query_ids must contain non-empty strings")
        if len(benchmark_refs) != len(set(item for item in benchmark_refs if isinstance(item, str))):
            errors.append(f"routing entry {routing_id or index} benchmark_query_ids must be unique")
        routing_benchmark_query_ids.extend(
            query_id for query_id in benchmark_refs if isinstance(query_id, str) and query_id
        )

        source = entry.get("source")
        if not isinstance(source, dict):
            errors.append(f"routing entry {routing_id or index} source must be an object")
            source = {}
        source_file = source.get("file")
        source_scenario_id = source.get("scenario_id")
        if not safe_relative_path(source_file):
            errors.append(f"routing entry {routing_id or index} has unsafe source file path")
        elif not (root / source_file).is_file():
            errors.append(f"routing entry {routing_id or index} source file does not resolve: {source_file}")
        else:
            if source_file not in source_cache:
                source_cache[source_file] = _read_json(root / source_file, errors, source_file) or {}
            source_scenarios = source_cache[source_file].get("scenarios", [])
            if not isinstance(source_scenarios, list):
                errors.append(f"routing source file {source_file} must contain a scenarios list")
                source_scenarios = []
            matched = next(
                (item for item in source_scenarios
                 if isinstance(item, dict) and item.get("id") == source_scenario_id),
                None,
            )
            if matched is None:
                errors.append(
                    f"routing entry {routing_id or index} does not resolve scenario "
                    f"{source_scenario_id!r} in {source_file}"
                )
            elif matched.get("problem") != entry.get("problem"):
                errors.append(
                    f"routing entry {routing_id or index} problem text does not match its source scenario"
                )

        answer_references = entry.get("answer_references")
        if not isinstance(answer_references, list) or not answer_references:
            errors.append(f"routing entry {routing_id or index} must have answer_references")
            answer_references = []
        for answer_index, answer_ref in enumerate(answer_references, start=1):
            label = f"routing entry {routing_id or index} answer reference {answer_index}"
            if not isinstance(answer_ref, dict):
                errors.append(f"{label} must be an object")
                continue
            answer_file = answer_ref.get("file")
            heading = answer_ref.get("heading")
            if not safe_relative_path(answer_file):
                errors.append(f"{label} has unsafe file path")
            elif not (root / answer_file).is_file():
                errors.append(f"{label} file does not resolve: {answer_file}")
            else:
                if answer_file not in markdown_cache:
                    try:
                        markdown_cache[answer_file] = (root / answer_file).read_text(encoding="utf-8")
                    except OSError as exc:
                        errors.append(f"{label} cannot read {answer_file}: {exc}")
                        markdown_cache[answer_file] = ""
                if not isinstance(heading, str) or not heading or heading not in markdown_cache[answer_file]:
                    errors.append(f"{label} heading does not resolve in {answer_file}: {heading!r}")

        for path_field in ("supporting_documents", "evidence_refs"):
            values = entry.get(path_field)
            if not isinstance(values, list):
                errors.append(f"routing entry {routing_id or index} {path_field} must be a list")
                continue
            for path_index, relative_path in enumerate(values, start=1):
                label = f"routing entry {routing_id or index} {path_field}[{path_index}]"
                if not safe_relative_path(relative_path):
                    errors.append(f"{label} must be a safe repository-relative path")
                elif not (root / relative_path).is_file():
                    errors.append(f"{label} does not resolve: {relative_path}")

        primary_sources = entry.get("primary_sources")
        if not isinstance(primary_sources, list) or not primary_sources:
            errors.append(f"routing entry {routing_id or index} must have primary_sources")
        else:
            for source_index, primary_source in enumerate(primary_sources, start=1):
                label = f"routing entry {routing_id or index} primary source {source_index}"
                if not isinstance(primary_source, str) or not primary_source:
                    errors.append(f"{label} must be a non-empty string")
                elif primary_source.startswith(("https://", "http://")):
                    _validate_url(primary_source, label, errors)
                elif not safe_relative_path(primary_source) or not (root / primary_source).is_file():
                    errors.append(f"{label} does not resolve to a safe repository-relative path: {primary_source}")

        evidence_refs = entry.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            errors.append(
                f"routing entry {routing_id or index} must have non-empty source-grounded evidence_refs"
            )
            evidence_refs = []
        primary_urls = {
            source for source in (primary_sources if isinstance(primary_sources, list) else [])
            if isinstance(source, str) and source.startswith("https://")
        }
        for evidence_index, evidence_path in enumerate(evidence_refs, start=1):
            label = f"routing entry {routing_id or index} evidence_refs[{evidence_index}]"
            if not safe_relative_path(evidence_path):
                errors.append(f"{label} must be a safe repository-relative path")
                continue
            evidence_file = root / evidence_path
            if not evidence_file.is_file():
                continue
            try:
                evidence_text = evidence_file.read_text(encoding="utf-8-sig")
            except OSError as exc:
                errors.append(f"{label} cannot be read: {exc}")
                continue
            frontmatter_parts = evidence_text.split("---", 2)
            metadata = frontmatter_parts[1].splitlines() if len(frontmatter_parts) >= 3 else []
            if not any(line.strip() == "type: evidence" for line in metadata):
                errors.append(f"{label} must point to a type: evidence record")
            if not any(line.strip() == "status: verified" for line in metadata):
                errors.append(f"{label} must point to a verified evidence record")
            if primary_urls and not any(url in evidence_text for url in primary_urls):
                errors.append(
                    f"{label} does not cite any URL declared in routing primary_sources"
                )

        for field in ("service_fit", "guardrails"):
            values = entry.get(field)
            if not isinstance(values, list) or not values:
                errors.append(f"routing entry {routing_id or index} {field} must be a non-empty list")

    if len(routing_ids) != len(set(routing_ids)):
        errors.append("problem-answer routing IDs must be unique")

    for rel in (REFERENCE_PACK, PROBLEM_LIBRARY):
        path = root / rel
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            errors.append(f"missing required file: {rel}")
            continue
        except OSError as exc:
            errors.append(f"cannot read {rel}: {exc}")
            continue
        for offset, url in _urls_in_text(content):
            line = content.count("\n", 0, offset) + 1
            _validate_url(url, f"{rel}:{line}", errors)

    benchmark = _read_json(root / BENCHMARK, errors, BENCHMARK) or {}
    if benchmark.get("schema") != BENCHMARK_SCHEMA:
        errors.append("unexpected AI visibility benchmark schema")
    queries = benchmark.get("queries", [])
    if not isinstance(queries, list) or not queries:
        errors.append("AI visibility benchmark must contain queries")
        queries = []
    query_ids: list[str] = []
    required_query_fields = ("id", "cluster", "language", "region", "query", "expected_facts", "preferred_sources", "must_not_claim", "status")
    for index, query in enumerate(queries, start=1):
        if not isinstance(query, dict):
            errors.append(f"benchmark query {index} must be an object")
            continue
        for field in required_query_fields:
            if field not in query or query[field] in (None, "", []):
                errors.append(f"benchmark query {index} missing required field: {field}")
        qid = query.get("id")
        if isinstance(qid, str) and qid:
            query_ids.append(qid)
        if query.get("status") != "not_run":
            errors.append(f"benchmark query {qid or index} must remain not_run until evidence is collected")
        sources = query.get("preferred_sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"benchmark query {qid or index} must have preferred_sources")
            continue
        for source_index, source in enumerate(sources, start=1):
            label = f"benchmark query {qid or index} source {source_index}"
            if not isinstance(source, str) or not source:
                errors.append(f"{label} must be a non-empty string")
            elif source.startswith(("https://", "http://")):
                _validate_url(source, label, errors)
            elif source.startswith("/") or ".." in Path(source).parts:
                errors.append(f"{label} must be a safe repository-relative path: {source}")
            elif not (root / source).is_file():
                errors.append(f"{label} does not resolve to a repository file: {source}")
    if len(query_ids) != len(set(query_ids)):
        errors.append("benchmark query IDs must be unique")

    known_query_ids = set(query_ids)
    unknown_route_queries = sorted(set(routing_benchmark_query_ids) - known_query_ids)
    for query_id in unknown_route_queries:
        errors.append(f"routing index references unknown benchmark query: {query_id}")

    problem_query_ids = {
        query.get("id") for query in queries
        if isinstance(query, dict) and query.get("cluster") == "problem_solving"
        and isinstance(query.get("id"), str)
    }
    mapped_problem_queries = set(routing_benchmark_query_ids) & problem_query_ids
    for query_id in sorted(problem_query_ids - mapped_problem_queries):
        errors.append(f"problem-solving benchmark query is not mapped to an answer route: {query_id}")

    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        print("Problem-solution knowledge validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    library = json.loads((ROOT / LIBRARY).read_text(encoding="utf-8"))
    benchmark = json.loads((ROOT / BENCHMARK).read_text(encoding="utf-8"))
    routing = json.loads((ROOT / ROUTING_INDEX).read_text(encoding="utf-8"))
    print(
        "Problem-solution knowledge PASS: "
        f"{len(library['scenarios'])} scenarios, {len(routing['entries'])} routing entries, "
        f"{len(benchmark['queries'])} unrun queries; "
        "preferred-source paths resolve and source URLs are canonical."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
