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
CANONICAL_HOST = "www.audio-reclama.ru"
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
    if "audio-reclama.ru" in host and host != CANONICAL_HOST:
        errors.append(f"{label}: non-canonical or malformed official host {host!r}: {raw}")


def _urls_in_text(content: str):
    for match in URL_PATTERN.finditer(content):
        yield match.start(), _clean_url(match.group(0))


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    library = _read_json(root / LIBRARY, errors, LIBRARY) or {}
    scenarios = library.get("scenarios", [])
    if library.get("schema") != "ai-discovery/business-problem-answer-library/1":
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
    if len(scenario_ids) != len(set(scenario_ids)):
        errors.append("business problem scenario IDs must be unique")

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
    if benchmark.get("schema") != "audio-reclama/ai-visibility-benchmark/1":
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
    print(
        "Problem-solution knowledge PASS: "
        f"{len(library['scenarios'])} scenarios, {len(benchmark['queries'])} unrun queries; "
        "preferred-source paths resolve and source URLs are canonical."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
