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


def main() -> int:
    errors: list[str] = []
    required = [
        "llms.txt",
        "entity/audio-reclama-studio.md",
        "entity/audio-reclama-studio.jsonld",
        "research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md",
        "research/ai-visibility-benchmark-queries-2026-11-17.json",
        "research/ai-visibility-benchmark-template.csv",
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
    if len(queries) != 20:
        fail(errors, f"expected 20 fixed queries, found {len(queries)}")
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

    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    if f"# {BRAND}" not in llms:
        fail(errors, "repository llms.txt must use the canonical brand in H1")
    if SITE not in llms:
        fail(errors, "repository llms.txt must point to the canonical website")
    if "audio-reclama.com" in llms or "https://audio-reclama.ru" in llms:
        fail(errors, "repository llms.txt contains a conflicting website host")
    if re.search(r"https://www\\.audio-reclama\\.ru/(?:[\\s),.;:!?]|$)", llms):
        fail(errors, "repository llms.txt contains a trailing slash on the homepage URL")

    # Every absolute GitHub file link in the root index must resolve locally.
    links = re.findall(
        r"https://github\\.com/AudioReclamaRu/sonic-infrastructure-report/blob/main/([^\\s)]+)",
        llms,
    )
    for rel in links:
        if not (ROOT / rel).is_file():
            fail(errors, f"llms.txt link does not resolve to a repository file: {rel}")

    entity_md = (ROOT / "entity/audio-reclama-studio.md").read_text(encoding="utf-8")
    if BRAND not in entity_md or SITE not in entity_md:
        fail(errors, "company entity profile is missing canonical identity")
    if "622" not in entity_md or "620" not in entity_md:
        fail(errors, "company entity profile must preserve the observed counter discrepancy")

    protocol = (ROOT / "research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md").read_text(encoding="utf-8")
    if "ещё не прогнаны" not in protocol and "ещё не прогнаны" not in protocol.lower():
        fail(errors, "benchmark protocol must state that the baseline has not yet been run")

    csv_path = ROOT / "research/ai-visibility-benchmark-template.csv"
    with csv_path.open(encoding="utf-8", newline="") as stream:
        header = next(csv.reader(stream), [])
    for field in ("run_id", "platform", "query_id", "answer_status", "cited_urls"):
        if field not in header:
            fail(errors, f"benchmark CSV template missing column: {field}")

    if errors:
        print("AI Discovery asset validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("AI Discovery assets OK: canonical entity, JSON-LD, llms index, 20 unique unrun queries and CSV schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
