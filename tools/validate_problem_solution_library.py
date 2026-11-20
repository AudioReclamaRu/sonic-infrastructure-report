#!/usr/bin/env python3
"""Validate problem-solution knowledge, source URLs and benchmark references."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
try:
    from tools.ai_discovery_source_retrieval import (
        evaluate as evaluate_source_retrieval,
        validate_report as validate_source_retrieval_report,
    )
except ImportError:
    from ai_discovery_source_retrieval import (
        evaluate as evaluate_source_retrieval,
        validate_report as validate_source_retrieval_report,
    )

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = "problem-solutions/business-problem-answer-library-2026-11-17.json"
REFERENCE_PACK = "problem-solutions/AI_ANSWER_REFERENCE_PACK_2026-11-17.md"
PROBLEM_LIBRARY = "problem-solutions/BUSINESS_PROBLEM_AUDIO_ANSWER_LIBRARY_2026-11-17.md"
BENCHMARK = "research/ai-visibility-benchmark-queries-2026-11-17.json"
VOICE_ASSET_LIBRARY = "problem-solutions/voice-asset-operations-answer-library-2026-11-18.json"
ROUTING_INDEX = "problem-solutions/AI_PROBLEM_ANSWER_ROUTING_INDEX_2026-11-18.json"
COMMERCIAL_SERVICE_ROUTES = "problem-solutions/AI_COMMERCIAL_SERVICE_ROUTING_2026-11-20.json"
COMMERCIAL_SERVICE_PACK = "problem-solutions/AI_COMMERCIAL_SERVICE_ANSWER_PACK_2026-11-20.md"
COMMERCIAL_SERVICE_SCHEMA = "studio/ai-commercial-service-routing/1"
EXPERTISE_ANSWER_PACK = "problem-solutions/AI_EXPERTISE_EVIDENCE_ANSWER_PACK_2026-11-20.md"
EXPERTISE_ROUTES = "problem-solutions/AI_EXPERTISE_EVIDENCE_ROUTING_2026-11-20.json"
EXPERTISE_ROUTING_SCHEMA = "studio/ai-expertise-evidence-routing/1"
ENTITY_ANSWER_PACK = "problem-solutions/AI_ENTITY_ANSWER_PACK_2026-11-20.md"
ENTITY_ROUTES = "problem-solutions/AI_ENTITY_ANSWER_ROUTING_2026-11-20.json"
ENTITY_ROUTING_SCHEMA = "studio/ai-entity-answer-routing/1"
CLAIM_SUPPORT_MATRIX = "problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json"
CLAIM_SUPPORT_SCHEMA = "studio/ai-discovery-claim-support-matrix/1"
ANSWER_COVERAGE_AUDIT = "problem-solutions/AI_DISCOVERY_ANSWER_COVERAGE_AUDIT_2026-11-20.json"
ANSWER_COVERAGE_SCHEMA = "studio/ai-discovery-answer-coverage-audit/1"
SOURCE_RETRIEVAL_SCRIPT = "tools/ai_discovery_source_retrieval.py"
RETRIEVAL_EVALUATION = "problem-solutions/AI_DISCOVERY_RETRIEVAL_EVALUATION_2026-11-20.json"
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
        "supporting_documents", "evidence_refs", "primary_sources", "benchmark_query_ids",
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

        # Bind every route's company-specific primary source to at least one
        # repository evidence record. A URL alone is not an auditable evidence edge.
        route_evidence_sources: set[str] = set()
        for path_field in ("supporting_documents", "evidence_refs"):
            values = entry.get(path_field)
            if not isinstance(values, list):
                errors.append(f"routing entry {routing_id or index} {path_field} must be a list")
                continue
            if path_field == "evidence_refs" and not values:
                errors.append(f"routing entry {routing_id or index} must have non-empty evidence_refs")
                continue
            for path_index, relative_path in enumerate(values, start=1):
                label = f"routing entry {routing_id or index} {path_field}[{path_index}]"
                if not safe_relative_path(relative_path):
                    errors.append(f"{label} must be a safe repository-relative path")
                elif path_field == "evidence_refs" and not relative_path.startswith("evidence/"):
                    errors.append(f"{label} must reference a file inside evidence/")
                elif not (root / relative_path).is_file():
                    errors.append(f"{label} does not resolve: {relative_path}")
                elif path_field == "evidence_refs":
                    try:
                        evidence_text = (root / relative_path).read_text(encoding="utf-8")
                    except OSError as exc:
                        errors.append(f"{label} cannot read evidence record: {exc}")
                        continue
                    source_matches = list(re.finditer(
                        r"^\*\*Primary source:\*\*\s*(https?://\S+)\s*$",
                        evidence_text,
                        flags=re.MULTILINE,
                    ))
                    if not source_matches:
                        errors.append(f"{label} has no explicit Primary source URL")
                    for match in source_matches:
                        evidence_source = _clean_url(match.group(1))
                        _validate_url(evidence_source, f"{label} Primary source", errors)
                        route_evidence_sources.add(evidence_source)

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
                    normalized_source = _clean_url(primary_source)
                    if normalized_source not in route_evidence_sources:
                        errors.append(
                            f"{label} is not covered by any linked evidence_refs record: {primary_source}"
                        )
                else:
                    errors.append(
                        f"{label} must be an absolute HTTPS URL; place internal repository files under supporting_documents: {primary_source}"
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

    # Every commercial-service benchmark query needs a concise, source-grounded
    # answer route. This is separate from problem-solving routes: buyers asking
    # "does the studio provide X?" need direct service answers as well as playbooks.
    service_routes = _read_json(root / COMMERCIAL_SERVICE_ROUTES, errors, COMMERCIAL_SERVICE_ROUTES) or {}
    if service_routes.get("schema") != COMMERCIAL_SERVICE_SCHEMA:
        errors.append("unexpected commercial service routing schema")
    service_entries = service_routes.get("entries", [])
    if not isinstance(service_entries, list) or not service_entries:
        errors.append("commercial service routing index must contain entries")
        service_entries = []
    if service_routes.get("entry_count") != len(service_entries):
        errors.append("commercial service routing entry_count must equal actual entries")
    try:
        service_pack = (root / COMMERCIAL_SERVICE_PACK).read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read commercial service answer pack: {exc}")
        service_pack = ""

    service_query_map = {
        query.get("id"): query for query in queries
        if isinstance(query, dict) and query.get("cluster") == "commercial_service"
        and isinstance(query.get("id"), str)
    }
    routed_service_ids: list[str] = []
    service_route_ids: list[str] = []
    for route_index, route in enumerate(service_entries, start=1):
        if not isinstance(route, dict):
            errors.append(f"commercial service route {route_index} must be an object")
            continue
        for field in ("routing_id", "benchmark_query_id", "question", "answer_heading",
                      "primary_sources", "evidence_refs", "service_fit", "guardrails"):
            if field not in route or route[field] in (None, "", []):
                errors.append(f"commercial service route {route_index} missing required field: {field}")
        routing_id = route.get("routing_id")
        if isinstance(routing_id, str) and routing_id:
            service_route_ids.append(routing_id)
        query_id = route.get("benchmark_query_id")
        if isinstance(query_id, str) and query_id:
            routed_service_ids.append(query_id)
        query = service_query_map.get(query_id)
        if query is None:
            errors.append(
                f"commercial service route {routing_id or route_index} references unknown or non-commercial benchmark query: {query_id}"
            )
        elif query.get("query") != route.get("question"):
            errors.append(
                f"commercial service route {routing_id or route_index} question does not match benchmark query {query_id}"
            )
        heading = route.get("answer_heading")
        if not isinstance(heading, str) or not heading or heading not in service_pack:
            errors.append(f"commercial service route {routing_id or route_index} answer heading does not resolve: {heading!r}")

        evidence_sources: set[str] = set()
        evidence_refs = route.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            errors.append(f"commercial service route {routing_id or route_index} must have evidence_refs")
            evidence_refs = []
        for evidence_index, evidence_ref in enumerate(evidence_refs, start=1):
            label = f"commercial service route {routing_id or route_index} evidence_refs[{evidence_index}]"
            if not safe_relative_path(evidence_ref) or not evidence_ref.startswith("evidence/"):
                errors.append(f"{label} must be a safe path inside evidence/")
            elif not (root / evidence_ref).is_file():
                errors.append(f"{label} does not resolve: {evidence_ref}")
            else:
                try:
                    evidence_text = (root / evidence_ref).read_text(encoding="utf-8")
                except OSError as exc:
                    errors.append(f"{label} cannot be read: {exc}")
                    continue
                evidence_lines = [
                    line for line in evidence_text.splitlines()
                    if line.startswith("**Primary source:**")
                ]
                if not evidence_lines:
                    errors.append(f"{label} has no explicit Primary source URL")
                for evidence_line in evidence_lines:
                    source_url = _clean_url(evidence_line.split("**Primary source:**", 1)[1].strip())
                    _validate_url(source_url, f"{label} Primary source", errors)
                    evidence_sources.add(source_url)

        primary_sources = route.get("primary_sources")
        if not isinstance(primary_sources, list) or not primary_sources:
            errors.append(f"commercial service route {routing_id or route_index} must have primary_sources")
            primary_sources = []
        for source_index, source_url in enumerate(primary_sources, start=1):
            label = f"commercial service route {routing_id or route_index} primary_sources[{source_index}]"
            if not isinstance(source_url, str) or not source_url.startswith("https://"):
                errors.append(f"{label} must be an absolute HTTPS URL")
                continue
            _validate_url(source_url, label, errors)
            if _clean_url(source_url) not in evidence_sources:
                errors.append(f"{label} is not covered by any linked evidence_refs record: {source_url}")

        supporting_documents = route.get("supporting_documents", [])
        if not isinstance(supporting_documents, list):
            errors.append(f"commercial service route {routing_id or route_index} supporting_documents must be a list")
        else:
            for support_index, support_path in enumerate(supporting_documents, start=1):
                label = f"commercial service route {routing_id or route_index} supporting_documents[{support_index}]"
                if not safe_relative_path(support_path) or not (root / support_path).is_file():
                    errors.append(f"{label} does not resolve to a safe repository file: {support_path}")

        for field in ("service_fit", "guardrails"):
            values = route.get(field)
            if not isinstance(values, list) or not values:
                errors.append(f"commercial service route {routing_id or route_index} {field} must be a non-empty list")

    if len(service_route_ids) != len(set(service_route_ids)):
        errors.append("commercial service routing IDs must be unique")
    if len(routed_service_ids) != len(set(routed_service_ids)):
        errors.append("commercial service benchmark query IDs must be unique")
    missing_service_routes = sorted(set(service_query_map) - set(routed_service_ids))
    for query_id in missing_service_routes:
        errors.append(f"commercial-service benchmark query is not mapped to an answer route: {query_id}")
    unknown_service_routes = sorted(set(routed_service_ids) - set(service_query_map))
    for query_id in unknown_service_routes:
        errors.append(f"commercial service routing index references unknown query: {query_id}")

    # Map every expertise/evidence benchmark prompt to a concise answer and
    # typed repository knowledge. Keep studio-authored positions and standards
    # distinct from external/legal evidence; do not call internal policy a law.
    expertise_routes = _read_json(root / EXPERTISE_ROUTES, errors, EXPERTISE_ROUTES) or {}
    if expertise_routes.get("schema") != EXPERTISE_ROUTING_SCHEMA:
        errors.append("unexpected expertise/evidence routing schema")
    expertise_entries = expertise_routes.get("entries", [])
    if not isinstance(expertise_entries, list) or not expertise_entries:
        errors.append("expertise/evidence routing index must contain entries")
        expertise_entries = []
    if expertise_routes.get("entry_count") != len(expertise_entries):
        errors.append("expertise/evidence routing entry_count must equal actual entries")
    try:
        expertise_pack = (root / EXPERTISE_ANSWER_PACK).read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read expertise/evidence answer pack: {exc}")
        expertise_pack = ""

    expertise_query_map = {
        query.get("id"): query for query in queries
        if isinstance(query, dict) and query.get("cluster") == "expertise_and_evidence"
        and isinstance(query.get("id"), str)
    }
    routed_expertise_ids: list[str] = []
    expertise_route_ids: list[str] = []
    for route_index, route in enumerate(expertise_entries, start=1):
        if not isinstance(route, dict):
            errors.append(f"expertise/evidence route {route_index} must be an object")
            continue
        for field in ("routing_id", "benchmark_query_id", "question", "answer_heading",
                      "knowledge_sources", "source_classes", "guardrails"):
            if field not in route or route[field] in (None, "", []):
                errors.append(f"expertise/evidence route {route_index} missing required field: {field}")
        routing_id = route.get("routing_id")
        if isinstance(routing_id, str) and routing_id:
            expertise_route_ids.append(routing_id)
        query_id = route.get("benchmark_query_id")
        if isinstance(query_id, str) and query_id:
            routed_expertise_ids.append(query_id)
        query = expertise_query_map.get(query_id)
        if query is None:
            errors.append(
                f"expertise/evidence route {routing_id or route_index} references unknown or non-expertise benchmark query: {query_id}"
            )
        elif query.get("query") != route.get("question"):
            errors.append(
                f"expertise/evidence route {routing_id or route_index} question does not match benchmark query {query_id}"
            )
        heading = route.get("answer_heading")
        if not isinstance(heading, str) or not heading or heading not in expertise_pack:
            errors.append(f"expertise/evidence route {routing_id or route_index} answer heading does not resolve: {heading!r}")

        knowledge_sources = route.get("knowledge_sources")
        if not isinstance(knowledge_sources, list) or not knowledge_sources:
            errors.append(f"expertise/evidence route {routing_id or route_index} must have knowledge_sources")
        else:
            for source_index, source_path in enumerate(knowledge_sources, start=1):
                label = f"expertise/evidence route {routing_id or route_index} knowledge_sources[{source_index}]"
                if not safe_relative_path(source_path) or not (root / source_path).is_file():
                    errors.append(f"{label} does not resolve to a safe repository file: {source_path}")

        source_classes = route.get("source_classes")
        if not isinstance(source_classes, list) or not source_classes:
            errors.append(f"expertise/evidence route {routing_id or route_index} source_classes must be a non-empty list")

        evidence_sources: set[str] = set()
        evidence_refs = route.get("evidence_refs", [])
        if not isinstance(evidence_refs, list):
            errors.append(f"expertise/evidence route {routing_id or route_index} evidence_refs must be a list")
            evidence_refs = []
        for evidence_index, evidence_ref in enumerate(evidence_refs, start=1):
            label = f"expertise/evidence route {routing_id or route_index} evidence_refs[{evidence_index}]"
            if not safe_relative_path(evidence_ref) or not evidence_ref.startswith("evidence/"):
                errors.append(f"{label} must be a safe path inside evidence/")
            elif not (root / evidence_ref).is_file():
                errors.append(f"{label} does not resolve: {evidence_ref}")
            else:
                try:
                    evidence_text = (root / evidence_ref).read_text(encoding="utf-8")
                except OSError as exc:
                    errors.append(f"{label} cannot be read: {exc}")
                    continue
                evidence_lines = [
                    line for line in evidence_text.splitlines()
                    if line.startswith("**Primary source:**")
                ]
                if not evidence_lines:
                    errors.append(f"{label} has no explicit Primary source URL")
                for evidence_line in evidence_lines:
                    source_url = _clean_url(evidence_line.split("**Primary source:**", 1)[1].strip())
                    _validate_url(source_url, f"{label} Primary source", errors)
                    evidence_sources.add(source_url)

        public_sources = route.get("public_source_urls", [])
        if not isinstance(public_sources, list):
            errors.append(f"expertise/evidence route {routing_id or route_index} public_source_urls must be a list")
            public_sources = []
        for source_index, source_url in enumerate(public_sources, start=1):
            label = f"expertise/evidence route {routing_id or route_index} public_source_urls[{source_index}]"
            if not isinstance(source_url, str) or not source_url.startswith("https://"):
                errors.append(f"{label} must be an absolute HTTPS URL")
                continue
            _validate_url(source_url, label, errors)
            if _clean_url(source_url) not in evidence_sources:
                errors.append(f"{label} is not covered by any linked evidence_refs record: {source_url}")

        guardrails = route.get("guardrails")
        if not isinstance(guardrails, list) or not guardrails:
            errors.append(f"expertise/evidence route {routing_id or route_index} guardrails must be a non-empty list")

    if len(expertise_route_ids) != len(set(expertise_route_ids)):
        errors.append("expertise/evidence routing IDs must be unique")
    if len(routed_expertise_ids) != len(set(routed_expertise_ids)):
        errors.append("expertise/evidence benchmark query IDs must be unique")
    missing_expertise_routes = sorted(set(expertise_query_map) - set(routed_expertise_ids))
    for query_id in missing_expertise_routes:
        errors.append(f"expertise/evidence benchmark query is not mapped to an answer route: {query_id}")
    unknown_expertise_routes = sorted(set(routed_expertise_ids) - set(expertise_query_map))
    for query_id in unknown_expertise_routes:
        errors.append(f"expertise/evidence routing index references unknown query: {query_id}")

    # Route all brand/entity benchmark prompts to exact, evidence-aware entity
    # answers. Dated snapshots for contacts and counters must retain their caveats.
    entity_routes = _read_json(root / ENTITY_ROUTES, errors, ENTITY_ROUTES) or {}
    if entity_routes.get("schema") != ENTITY_ROUTING_SCHEMA:
        errors.append("unexpected brand/entity routing schema")
    entity_entries = entity_routes.get("entries", [])
    if not isinstance(entity_entries, list) or not entity_entries:
        errors.append("brand/entity routing index must contain entries")
        entity_entries = []
    if entity_routes.get("entry_count") != len(entity_entries):
        errors.append("brand/entity routing entry_count must equal actual entries")
    try:
        entity_pack = (root / ENTITY_ANSWER_PACK).read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read brand/entity answer pack: {exc}")
        entity_pack = ""

    entity_query_map = {
        query.get("id"): query for query in queries
        if isinstance(query, dict) and query.get("cluster") == "brand_entity"
        and isinstance(query.get("id"), str)
    }
    routed_entity_ids: list[str] = []
    entity_route_ids: list[str] = []
    for route_index, route in enumerate(entity_entries, start=1):
        if not isinstance(route, dict):
            errors.append(f"brand/entity route {route_index} must be an object")
            continue
        for field in ("routing_id", "benchmark_query_id", "question", "answer_heading",
                      "knowledge_sources", "guardrails"):
            if field not in route or route[field] in (None, "", []):
                errors.append(f"brand/entity route {route_index} missing required field: {field}")
        routing_id = route.get("routing_id")
        if isinstance(routing_id, str) and routing_id:
            entity_route_ids.append(routing_id)
        query_id = route.get("benchmark_query_id")
        if isinstance(query_id, str) and query_id:
            routed_entity_ids.append(query_id)
        query = entity_query_map.get(query_id)
        if query is None:
            errors.append(
                f"brand/entity route {routing_id or route_index} references unknown or non-brand benchmark query: {query_id}"
            )
        elif query.get("query") != route.get("question"):
            errors.append(
                f"brand/entity route {routing_id or route_index} question does not match benchmark query {query_id}"
            )
        heading = route.get("answer_heading")
        if not isinstance(heading, str) or not heading or heading not in entity_pack:
            errors.append(f"brand/entity route {routing_id or route_index} answer heading does not resolve: {heading!r}")

        knowledge_sources = route.get("knowledge_sources")
        if not isinstance(knowledge_sources, list) or not knowledge_sources:
            errors.append(f"brand/entity route {routing_id or route_index} must have knowledge_sources")
        else:
            for source_index, source_path in enumerate(knowledge_sources, start=1):
                label = f"brand/entity route {routing_id or route_index} knowledge_sources[{source_index}]"
                if not safe_relative_path(source_path) or not (root / source_path).is_file():
                    errors.append(f"{label} does not resolve to a safe repository file: {source_path}")

        source_classes = route.get("source_classes", [])
        if not isinstance(source_classes, list) or not source_classes:
            errors.append(f"brand/entity route {routing_id or route_index} source_classes must be a non-empty list")

        evidence_sources: set[str] = set()
        evidence_refs = route.get("evidence_refs", [])
        if not isinstance(evidence_refs, list):
            errors.append(f"brand/entity route {routing_id or route_index} evidence_refs must be a list")
            evidence_refs = []
        for evidence_index, evidence_ref in enumerate(evidence_refs, start=1):
            label = f"brand/entity route {routing_id or route_index} evidence_refs[{evidence_index}]"
            if not safe_relative_path(evidence_ref) or not evidence_ref.startswith("evidence/"):
                errors.append(f"{label} must be a safe path inside evidence/")
            elif not (root / evidence_ref).is_file():
                errors.append(f"{label} does not resolve: {evidence_ref}")
            else:
                try:
                    evidence_text = (root / evidence_ref).read_text(encoding="utf-8")
                except OSError as exc:
                    errors.append(f"{label} cannot be read: {exc}")
                    continue
                evidence_lines = [
                    line for line in evidence_text.splitlines()
                    if line.startswith("**Primary source:**") or line.startswith("- https://")
                ]
                if not evidence_lines:
                    errors.append(f"{label} has no explicit Primary source URL")
                for evidence_line in evidence_lines:
                    source_value = evidence_line.split("**Primary source:**", 1)[1].strip() if evidence_line.startswith("**Primary source:**") else evidence_line.lstrip("- ").strip()
                    source_url = _clean_url(source_value)
                    _validate_url(source_url, f"{label} Primary source", errors)
                    evidence_sources.add(source_url)

        primary_sources = route.get("primary_sources", [])
        if not isinstance(primary_sources, list):
            errors.append(f"brand/entity route {routing_id or route_index} primary_sources must be a list")
            primary_sources = []
        for source_index, source_url in enumerate(primary_sources, start=1):
            label = f"brand/entity route {routing_id or route_index} primary_sources[{source_index}]"
            if not isinstance(source_url, str) or not source_url.startswith("https://"):
                errors.append(f"{label} must be an absolute HTTPS URL")
                continue
            _validate_url(source_url, label, errors)
            if _clean_url(source_url) not in evidence_sources:
                errors.append(f"{label} is not covered by any linked evidence_refs record: {source_url}")

        guardrails = route.get("guardrails")
        if not isinstance(guardrails, list) or not guardrails:
            errors.append(f"brand/entity route {routing_id or route_index} guardrails must be a non-empty list")

    if len(entity_route_ids) != len(set(entity_route_ids)):
        errors.append("brand/entity routing IDs must be unique")
    if len(routed_entity_ids) != len(set(routed_entity_ids)):
        errors.append("brand/entity benchmark query IDs must be unique")
    missing_entity_routes = sorted(set(entity_query_map) - set(routed_entity_ids))
    for query_id in missing_entity_routes:
        errors.append(f"brand/entity benchmark query is not mapped to an answer route: {query_id}")
    unknown_entity_routes = sorted(set(routed_entity_ids) - set(entity_query_map))
    for query_id in unknown_entity_routes:
        errors.append(f"brand/entity routing index references unknown query: {query_id}")


    # Every benchmark expected fact must resolve to explicit, typed source references.
    # This prevents a route from passing merely because it has an evidence file somewhere.
    claim_matrix = _read_json(root / CLAIM_SUPPORT_MATRIX, errors, CLAIM_SUPPORT_MATRIX) or {}
    if claim_matrix.get("schema") != CLAIM_SUPPORT_SCHEMA:
        errors.append("unexpected AI discovery claim-support matrix schema")
    claim_entries = claim_matrix.get("entries", [])
    if not isinstance(claim_entries, list):
        errors.append("AI discovery claim-support matrix entries must be a list")
        claim_entries = []
    if claim_matrix.get("query_count") != len(queries):
        errors.append("claim-support matrix query_count must equal benchmark query count")
    if len(claim_entries) != len(queries):
        errors.append("claim-support matrix must contain exactly one entry per benchmark query")
    semantic_review = claim_matrix.get("semantic_review", {})
    if not isinstance(semantic_review, dict):
        errors.append("claim-support matrix semantic_review must be an object")
        semantic_review = {}
    if semantic_review.get("status") != "first_pass_complete":
        errors.append("claim-support matrix must record a completed first-pass semantic review")
    if semantic_review.get("reviewed_at") != "2026-11-20":
        errors.append("claim-support matrix semantic review must have the expected review date")
    if semantic_review.get("reviewed_query_count") != len(queries):
        errors.append("semantic review must cover every benchmark query")
    if semantic_review.get("reviewed_claim_count") != claim_matrix.get("claim_count"):
        errors.append("semantic review claim count must match the claim-support matrix")
    for review_field in ("method", "limitations"):
        if not isinstance(semantic_review.get(review_field), list) or not semantic_review.get(review_field):
            errors.append(f"semantic review must include non-empty {review_field}")

    benchmark_by_id = {
        query.get("id"): query for query in queries
        if isinstance(query, dict) and isinstance(query.get("id"), str)
    }
    claim_query_ids: list[str] = []
    measured_claim_count = 0
    reviewed_claim_count = 0
    referenced_source_paths: set[str] = set()
    allowed_support_types = {"first_party_evidence", "internal_methodology", "mixed"}
    for entry_index, entry in enumerate(claim_entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"claim-support matrix entry {entry_index} must be an object")
            continue
        query_id = entry.get("benchmark_query_id")
        if not isinstance(query_id, str) or not query_id:
            errors.append(f"claim-support matrix entry {entry_index} missing benchmark_query_id")
            continue
        claim_query_ids.append(query_id)
        query = benchmark_by_id.get(query_id)
        if query is None:
            errors.append(f"claim-support matrix references unknown benchmark query: {query_id}")
            continue
        if entry.get("query_cluster") != query.get("cluster"):
            errors.append(f"claim-support matrix cluster does not match benchmark query {query_id}")
        claims = entry.get("claims")
        if not isinstance(claims, list):
            errors.append(f"claim-support matrix claims must be a list for {query_id}")
            continue
        expected_facts = query.get("expected_facts", [])
        measured_claim_count += len(claims)
        if len(claims) != len(expected_facts):
            errors.append(
                f"claim-support matrix must map every expected fact exactly once for {query_id}: "
                f"expected {len(expected_facts)}, found {len(claims)}"
            )
        seen_fact_indices: set[int] = set()
        for claim_index, claim in enumerate(claims, start=1):
            label = f"claim-support {query_id} fact {claim_index}"
            if not isinstance(claim, dict):
                errors.append(f"{label} must be an object")
                continue
            fact_index = claim.get("fact_index")
            if not isinstance(fact_index, int) or fact_index < 1 or fact_index > len(expected_facts):
                errors.append(f"{label} has invalid fact_index: {fact_index!r}")
            elif fact_index in seen_fact_indices:
                errors.append(f"{label} duplicates fact_index {fact_index}")
            else:
                seen_fact_indices.add(fact_index)
                if claim.get("expected_fact") != expected_facts[fact_index - 1]:
                    errors.append(f"{label} text does not exactly match benchmark expected_facts[{fact_index}]")

            support_type = claim.get("support_type")
            if support_type not in allowed_support_types:
                errors.append(f"{label} has unsupported support_type: {support_type!r}")
            scope_note = claim.get("scope_note")
            if not isinstance(scope_note, str) or not scope_note.strip():
                errors.append(f"{label} must have a non-empty scope_note")
            if claim.get("semantic_review_status") != "reviewed":
                errors.append(f"{label} must be marked reviewed after source-semantic review")
            review_note = claim.get("semantic_review_note")
            if not isinstance(review_note, str) or not review_note.strip():
                errors.append(f"{label} must have a non-empty semantic_review_note")
            else:
                reviewed_claim_count += 1
            source_refs = claim.get("source_refs")
            if not isinstance(source_refs, list) or not source_refs:
                errors.append(f"{label} must have source_refs")
                source_refs = []

            evidence_sources_count = 0
            internal_sources_count = 0
            for source_index, source_path in enumerate(source_refs, start=1):
                source_label = f"{label} source_refs[{source_index}]"
                if isinstance(source_path, str):
                    referenced_source_paths.add(source_path)
                if not safe_relative_path(source_path) or not (root / source_path).is_file():
                    errors.append(f"{source_label} does not resolve to a safe repository file: {source_path}")
                    continue
                if source_path not in query.get("preferred_sources", []):
                    errors.append(f"{source_label} is not declared in benchmark preferred_sources: {source_path}")
                if source_path.startswith("evidence/"):
                    evidence_sources_count += 1
                    try:
                        evidence_text = (root / source_path).read_text(encoding="utf-8")
                    except OSError as exc:
                        errors.append(f"{source_label} cannot be read: {exc}")
                        continue
                    source_lines = [
                        line.strip() for line in evidence_text.splitlines()
                        if line.startswith("**Primary source:**")
                        or line.startswith("**Primary sources:**")
                        or line.startswith("- https://")
                    ]
                    source_urls = []
                    for source_line in source_lines:
                        if source_line.startswith("**Primary source:**"):
                            value = source_line.split("**Primary source:**", 1)[1].strip()
                            if value.startswith("https://"):
                                source_urls.append(_clean_url(value))
                        elif source_line.startswith("- https://"):
                            source_urls.append(_clean_url(source_line[2:].strip()))
                    if not source_urls:
                        errors.append(f"{source_label} has no explicit HTTPS Primary source URL")
                    for source_url in source_urls:
                        _validate_url(source_url, f"{source_label} Primary source", errors)
                    status_match = re.search(r"^status:\s*([a-zA-Z0-9_-]+)\s*$", evidence_text, flags=re.MULTILINE)
                    evidence_status = status_match.group(1) if status_match else ""
                    if evidence_status not in {
                        "verified", "verified_first_party_snapshot", "indexed_first_party_snapshot"
                    }:
                        errors.append(f"{source_label} has unsupported or missing evidence status: {evidence_status!r}")
                    if evidence_status == "indexed_first_party_snapshot":
                        note = scope_note.lower() if isinstance(scope_note, str) else ""
                        if "индексирован" not in note and "crawl" not in note:
                            errors.append(
                                f"{label} must disclose indexed/crawl freshness when using {source_path}"
                            )
                else:
                    internal_sources_count += 1

            expected_support_type = (
                "mixed" if evidence_sources_count and internal_sources_count
                else "first_party_evidence" if evidence_sources_count
                else "internal_methodology" if internal_sources_count
                else None
            )
            if expected_support_type and support_type != expected_support_type:
                errors.append(
                    f"{label} support_type {support_type!r} does not match referenced source classes "
                    f"({expected_support_type})"
                )

    if len(claim_query_ids) != len(set(claim_query_ids)):
        errors.append("claim-support matrix benchmark_query_ids must be unique")
    missing_claim_queries = sorted(set(benchmark_by_id) - set(claim_query_ids))
    for query_id in missing_claim_queries:
        errors.append(f"benchmark expected facts have no claim-support entry: {query_id}")
    unknown_claim_queries = sorted(set(claim_query_ids) - set(benchmark_by_id))
    for query_id in unknown_claim_queries:
        errors.append(f"claim-support matrix references unknown benchmark query: {query_id}")
    if claim_matrix.get("claim_count") != measured_claim_count:
        errors.append(
            f"claim-support matrix claim_count must equal actual mapped facts ({measured_claim_count})"
        )
    if semantic_review.get("reviewed_claim_count") != reviewed_claim_count:
        errors.append(
            f"semantic review must mark every claim reviewed ({reviewed_claim_count} marked)"
        )
    if semantic_review.get("unique_source_documents") != len(referenced_source_paths):
        errors.append(
            "semantic review unique_source_documents must equal the actual unique claim source count"
        )
    if not isinstance(semantic_review.get("corrected_claim_mappings"), int) or semantic_review.get("corrected_claim_mappings") < 0:
        errors.append("semantic review corrected_claim_mappings must be a non-negative integer")

    # Check that every benchmark answer actually covers its expected facts and
    # that each forbidden-claim rule was reviewed against a resolvable answer section.
    answer_audit = _read_json(root / ANSWER_COVERAGE_AUDIT, errors, ANSWER_COVERAGE_AUDIT) or {}
    if answer_audit.get("schema") != ANSWER_COVERAGE_SCHEMA:
        errors.append("unexpected AI discovery answer-coverage audit schema")
    answer_entries = answer_audit.get("entries", [])
    if not isinstance(answer_entries, list):
        errors.append("AI discovery answer-coverage audit entries must be a list")
        answer_entries = []
    if answer_audit.get("query_count") != len(queries):
        errors.append("answer-coverage audit query_count must equal benchmark query count")
    if len(answer_entries) != len(queries):
        errors.append("answer-coverage audit must contain exactly one entry per benchmark query")

    answer_benchmark_ids: list[str] = []
    expected_fact_total = 0
    must_not_claim_total = 0
    reviewed_answer_files: set[str] = set()
    answer_text_cache: dict[str, str] = {}
    for entry_index, entry in enumerate(answer_entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"answer-coverage entry {entry_index} must be an object")
            continue
        query_id = entry.get("benchmark_query_id")
        if not isinstance(query_id, str) or not query_id:
            errors.append(f"answer-coverage entry {entry_index} missing benchmark_query_id")
            continue
        answer_benchmark_ids.append(query_id)
        query = benchmark_by_id.get(query_id)
        if query is None:
            errors.append(f"answer-coverage audit references unknown benchmark query: {query_id}")
            continue
        if entry.get("query_cluster") != query.get("cluster"):
            errors.append(f"answer-coverage cluster does not match benchmark query {query_id}")
        if entry.get("query") != query.get("query"):
            errors.append(f"answer-coverage query text does not match benchmark query {query_id}")
        if entry.get("overall_status") != "pass":
            errors.append(f"answer-coverage entry {query_id} is not marked pass")
        if entry.get("review_method") != "manual_answer_text_review":
            errors.append(f"answer-coverage entry {query_id} must record manual_answer_text_review")
        if entry.get("reviewed_at") != "2026-11-20":
            errors.append(f"answer-coverage entry {query_id} has an unexpected review date")

        answer_refs = entry.get("answer_references")
        if not isinstance(answer_refs, list) or not answer_refs:
            errors.append(f"answer-coverage entry {query_id} must have answer_references")
            answer_refs = []
        for ref_index, answer_ref in enumerate(answer_refs, start=1):
            label = f"answer-coverage {query_id} answer_references[{ref_index}]"
            if not isinstance(answer_ref, dict):
                errors.append(f"{label} must be an object")
                continue
            answer_file = answer_ref.get("file")
            heading = answer_ref.get("heading")
            if not safe_relative_path(answer_file) or not (root / answer_file).is_file():
                errors.append(f"{label} does not resolve to a safe repository file: {answer_file}")
                continue
            reviewed_answer_files.add(answer_file)
            if answer_file not in answer_text_cache:
                try:
                    answer_text_cache[answer_file] = (root / answer_file).read_text(encoding="utf-8")
                except OSError as exc:
                    errors.append(f"{label} cannot read {answer_file}: {exc}")
                    answer_text_cache[answer_file] = ""
            if not isinstance(heading, str) or not heading or heading not in answer_text_cache[answer_file]:
                errors.append(f"{label} heading does not resolve in {answer_file}: {heading!r}")

        alternative_refs = entry.get("retrieval_alternatives", [])
        if not isinstance(alternative_refs, list):
            errors.append(f"answer-coverage retrieval_alternatives must be a list for {query_id}")
            alternative_refs = []
        for ref_index, answer_ref in enumerate(alternative_refs, start=1):
            label = f"answer-coverage {query_id} retrieval_alternatives[{ref_index}]"
            if not isinstance(answer_ref, dict):
                errors.append(f"{label} must be an object")
                continue
            answer_file = answer_ref.get("file")
            heading = answer_ref.get("heading")
            reason = answer_ref.get("reason")
            if not safe_relative_path(answer_file) or not (root / answer_file).is_file():
                errors.append(f"{label} does not resolve to a safe repository file: {answer_file}")
                continue
            reviewed_answer_files.add(answer_file)
            if answer_file not in answer_text_cache:
                try:
                    answer_text_cache[answer_file] = (root / answer_file).read_text(encoding="utf-8")
                except OSError as exc:
                    errors.append(f"{label} cannot read {answer_file}: {exc}")
                    answer_text_cache[answer_file] = ""
            if not isinstance(heading, str) or not heading or heading not in answer_text_cache[answer_file]:
                errors.append(f"{label} heading does not resolve in {answer_file}: {heading!r}")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{label} must explain why the retrieval alternative is acceptable")

        fact_checks = entry.get("expected_fact_checks")
        expected_facts = query.get("expected_facts", [])
        if not isinstance(fact_checks, list):
            errors.append(f"answer-coverage expected_fact_checks must be a list for {query_id}")
            fact_checks = []
        expected_fact_total += len(fact_checks)
        if len(fact_checks) != len(expected_facts):
            errors.append(
                f"answer-coverage must check every expected fact for {query_id}: "
                f"expected {len(expected_facts)}, found {len(fact_checks)}"
            )
        seen_fact_indices: set[int] = set()
        for fact_index, fact_check in enumerate(fact_checks, start=1):
            label = f"answer-coverage {query_id} fact {fact_index}"
            if not isinstance(fact_check, dict):
                errors.append(f"{label} must be an object")
                continue
            index_value = fact_check.get("fact_index")
            if not isinstance(index_value, int) or index_value < 1 or index_value > len(expected_facts):
                errors.append(f"{label} has invalid fact_index: {index_value!r}")
            elif index_value in seen_fact_indices:
                errors.append(f"{label} duplicates fact_index {index_value}")
            else:
                seen_fact_indices.add(index_value)
                if fact_check.get("expected_fact") != expected_facts[index_value - 1]:
                    errors.append(f"{label} text does not match benchmark expected_facts[{index_value}]")
            if fact_check.get("status") != "covered":
                errors.append(f"{label} must be marked covered")
            review_note = fact_check.get("review_note")
            if not isinstance(review_note, str) or not review_note.strip():
                errors.append(f"{label} must have a non-empty review_note")

        forbidden_checks = entry.get("must_not_claim_checks")
        forbidden_claims = query.get("must_not_claim", [])
        if not isinstance(forbidden_checks, list):
            errors.append(f"answer-coverage must_not_claim_checks must be a list for {query_id}")
            forbidden_checks = []
        must_not_claim_total += len(forbidden_checks)
        if len(forbidden_checks) != len(forbidden_claims):
            errors.append(
                f"answer-coverage must check every must_not_claim for {query_id}: "
                f"expected {len(forbidden_claims)}, found {len(forbidden_checks)}"
            )
        seen_forbidden_indices: set[int] = set()
        for forbidden_index, forbidden_check in enumerate(forbidden_checks, start=1):
            label = f"answer-coverage {query_id} must_not_claim {forbidden_index}"
            if not isinstance(forbidden_check, dict):
                errors.append(f"{label} must be an object")
                continue
            index_value = forbidden_check.get("claim_index")
            if not isinstance(index_value, int) or index_value < 1 or index_value > len(forbidden_claims):
                errors.append(f"{label} has invalid claim_index: {index_value!r}")
            elif index_value in seen_forbidden_indices:
                errors.append(f"{label} duplicates claim_index {index_value}")
            else:
                seen_forbidden_indices.add(index_value)
                if forbidden_check.get("must_not_claim") != forbidden_claims[index_value - 1]:
                    errors.append(f"{label} text does not match benchmark must_not_claim[{index_value}]")
            if forbidden_check.get("status") not in {"not_asserted", "explicitly_guarded"}:
                errors.append(f"{label} must be marked not_asserted or explicitly_guarded")
            review_note = forbidden_check.get("review_note")
            if not isinstance(review_note, str) or not review_note.strip():
                errors.append(f"{label} must have a non-empty review_note")
        note = entry.get("review_note")
        if not isinstance(note, str) or not note.strip():
            errors.append(f"answer-coverage entry {query_id} must have a non-empty review_note")

    if len(answer_benchmark_ids) != len(set(answer_benchmark_ids)):
        errors.append("answer-coverage benchmark_query_ids must be unique")
    for query_id in sorted(set(benchmark_by_id) - set(answer_benchmark_ids)):
        errors.append(f"benchmark query has no answer-coverage review: {query_id}")
    for query_id in sorted(set(answer_benchmark_ids) - set(benchmark_by_id)):
        errors.append(f"answer-coverage references unknown benchmark query: {query_id}")
    expected_fact_count = sum(len(q.get("expected_facts", [])) for q in queries)
    must_not_claim_count = sum(len(q.get("must_not_claim", [])) for q in queries)
    if answer_audit.get("expected_fact_count") != expected_fact_count or expected_fact_total != expected_fact_count:
        errors.append("answer-coverage expected_fact_count must match all benchmark expected_facts")
    if answer_audit.get("must_not_claim_count") != must_not_claim_count or must_not_claim_total != must_not_claim_count:
        errors.append("answer-coverage must_not_claim_count must match all benchmark must_not_claims")

    try:
        try:
            from tools.ai_discovery_retrieval import validate_report as validate_retrieval_report
        except ImportError:
            from ai_discovery_retrieval import validate_report as validate_retrieval_report
        errors.extend(validate_retrieval_report(root))
    except (ImportError, OSError, ValueError) as exc:
        errors.append(f"AI Discovery retrieval evaluation could not run: {exc}")

    try:
        source_retrieval = evaluate_source_retrieval(root)
        source_metrics = source_retrieval.get("metrics", {})
        if source_metrics.get("mapped_source_documents") != semantic_review.get("unique_source_documents"):
            errors.append("mapped source-retrieval corpus must match the semantic-review source-document count")
        if source_metrics.get("expected_fact_count") != measured_claim_count:
            errors.append("source-retrieval expected_fact_count must match the claim-support matrix")
        errors.extend(validate_source_retrieval_report(root))
    except (ImportError, OSError, ValueError, TypeError) as exc:
        errors.append(f"AI Discovery mapped-source retrieval could not run: {exc}")

    return errors


def main() -> int:
    source_retrieval = evaluate_source_retrieval(ROOT)
    source_retrieval_baseline = {
        key: source_retrieval[key]
        for key in ("schema", "date", "status", "method", "corpus", "metrics", "source_class_aware")
    }
    source_retrieval_baseline["baseline_review_status"] = "reviewed"
    print(
        "SOURCE_RETRIEVAL_BASELINE "
        + json.dumps(source_retrieval_baseline, ensure_ascii=False, sort_keys=True)
    )
    errors = validate(ROOT)
    if errors:
        print("Problem-solution knowledge validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    library = json.loads((ROOT / LIBRARY).read_text(encoding="utf-8"))
    benchmark = json.loads((ROOT / BENCHMARK).read_text(encoding="utf-8"))
    routing = json.loads((ROOT / ROUTING_INDEX).read_text(encoding="utf-8"))
    benchmark_clusters = {
        query.get("id"): query.get("cluster")
        for query in benchmark.get("queries", [])
        if isinstance(query, dict) and isinstance(query.get("id"), str)
    }
    routed_ids = {
        query_id for entry in routing["entries"]
        for query_id in entry.get("benchmark_query_ids", [])
    }
    mapped_problem_count = sum(
        1 for query_id in routed_ids if benchmark_clusters.get(query_id) == "problem_solving"
    )
    mapped_trust_count = sum(
        1 for query_id in routed_ids if benchmark_clusters.get(query_id) == "expertise_and_evidence"
    )
    commercial_routes = json.loads((ROOT / COMMERCIAL_SERVICE_ROUTES).read_text(encoding="utf-8"))
    expertise_routes = json.loads((ROOT / EXPERTISE_ROUTES).read_text(encoding="utf-8"))
    entity_routes = json.loads((ROOT / ENTITY_ROUTES).read_text(encoding="utf-8"))
    claim_matrix = json.loads((ROOT / CLAIM_SUPPORT_MATRIX).read_text(encoding="utf-8"))
    semantic_review = claim_matrix.get("semantic_review", {})
    answer_audit = json.loads((ROOT / ANSWER_COVERAGE_AUDIT).read_text(encoding="utf-8"))
    retrieval_evaluation = json.loads((ROOT / RETRIEVAL_EVALUATION).read_text(encoding="utf-8"))
    retrieval_metrics = retrieval_evaluation["metrics"]
    source_metrics = source_retrieval["metrics"]
    source_class_aware = source_retrieval["source_class_aware"]
    print(
        "Problem-solution knowledge PASS: "
        f"{len(library['scenarios'])} problem scenarios, {len(routing['entries'])} problem routes, "
        f"{len(commercial_routes['entries'])} commercial-service routes, "
        f"{len(expertise_routes['entries'])} expertise/evidence routes, "
        f"{len(entity_routes['entries'])} brand/entity routes, "
        f"{mapped_problem_count} linked problem-solving prompts, "
        f"{mapped_trust_count} linked trust prompts, "
        f"{len(benchmark['queries'])} unrun benchmark queries, "
        f"{claim_matrix['claim_count']} semantically reviewed fact-level source mappings across "
        f"{semantic_review['unique_source_documents']} source documents, "
        f"{answer_audit['query_count']} reviewed answer texts, "
        f"{answer_audit['expected_fact_count']} expected facts covered and "
        f"{answer_audit['must_not_claim_count']} forbidden-claim checks, "
        f"{retrieval_metrics['acceptable_top_1']}/{retrieval_metrics['query_count']} acceptable retrieval top-1 and "
        f"{retrieval_metrics['primary_top_3']}/{retrieval_metrics['query_count']} canonical retrieval top-3; "
        f"{source_metrics['queries_with_mapped_source_top_3']}/{source_metrics['query_count']} queries retrieve a mapped source top-3; "
        f"{source_metrics['claims_with_mapped_source_top_3']}/{source_metrics['expected_fact_count']} facts top-3, "
        f"{source_metrics['claims_with_mapped_source_top_10']}/{source_metrics['expected_fact_count']} top-10; "
        f"first-party evidence top-5 (all evidence-bearing claims): {source_metrics['evidence_claims_with_evidence_top_5']}/{source_metrics['claims_with_first_party_evidence']}; "
        f"pure evidence top-5/top-10: {source_metrics['pure_first_party_evidence_top_5']}/{source_metrics['pure_first_party_claim_count']} and {source_metrics['pure_first_party_evidence_top_10']}/{source_metrics['pure_first_party_claim_count']}; "
        f"mixed evidence top-5: {source_metrics['mixed_claim_evidence_top_5']}/{source_metrics['mixed_claim_count']}; "
        f"class-aware facts with every required source class in top-3: "
        f"{source_class_aware['claims_all_required_classes_top_3']}/{source_metrics['expected_fact_count']}; "
        f"mixed claims with both classes in top-3: "
        f"{source_class_aware['mixed_claims_all_classes_top_3']}/{source_class_aware['mixed_claim_count']}; "
        "answer headings, knowledge sources, evidence bindings and guardrails resolve."
    )
    for weak in source_retrieval.get("weak_claims_top_10", []):
        print("SOURCE_RETRIEVAL_WEAK_FACT " + json.dumps(weak, ensure_ascii=False, sort_keys=True))
    for weak in source_retrieval.get("weak_pure_evidence_top_5", []):
        print("SOURCE_RETRIEVAL_WEAK_PURE_EVIDENCE " + json.dumps(weak, ensure_ascii=False, sort_keys=True))
    for weak in source_retrieval.get("weak_mixed_evidence_top_5", []):
        print("SOURCE_RETRIEVAL_WEAK_MIXED_EVIDENCE " + json.dumps(weak, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
