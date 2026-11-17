#!/usr/bin/env python3
"""Build and validate offline AI-visibility execution queues from frozen query modules.

This tool never contacts AI providers, changes a website, or performs measurements.
Queue rows are plans only; they must not be imported as completed benchmark observations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

QUEUE_FIELDS = (
    "queue_id", "module_id", "module_version", "query_id", "query", "intent",
    "country_code", "interface_locale", "prompt_language", "answer_language",
    "platform", "platform_surface", "measurement_mode", "platform_priority",
    "execution_status", "region_verification", "notes",
)
ALLOWED_MODES = {"consumer_ui", "model_api", "search_results_ui"}
PLANNED_STATUS = "NOT_TESTED"
REGION_STATUS = "UNVERIFIED"


def load_module(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("query module root must be a JSON object")
    if not isinstance(data.get("queries"), list) or not data["queries"]:
        raise ValueError("query module must contain a non-empty queries array")
    if not isinstance(data.get("platform_execution_order"), list) or not data["platform_execution_order"]:
        raise ValueError("query module must contain a non-empty platform_execution_order array")
    return data


def _market_fields(module: dict[str, Any]) -> dict[str, str]:
    market = module.get("market")
    if not isinstance(market, dict):
        raise ValueError("query module must define a market object")
    fields = {
        "country_code": market.get("country_code"),
        "interface_locale": market.get("interface_locale"),
        "prompt_language": market.get("prompt_language"),
        "answer_language": market.get("answer_language") or market.get("prompt_language"),
    }
    missing = [key for key, value in fields.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        raise ValueError("market fields missing: " + ", ".join(missing))
    return fields  # type: ignore[return-value]


def build_rows(module: dict[str, Any]) -> list[dict[str, str]]:
    market = _market_fields(module)
    module_id = str(module.get("schema") or "unspecified-module")
    version = str(module.get("version") or "unspecified")
    platforms = module["platform_execution_order"]
    queries = module["queries"]
    seen_platforms: set[str] = set()
    seen_queries: set[str] = set()
    rows: list[dict[str, str]] = []

    for query in queries:
        if not isinstance(query, dict):
            raise ValueError("each query entry must be an object")
        query_id = query.get("id")
        prompt = query.get("query")
        if not isinstance(query_id, str) or not query_id.strip():
            raise ValueError("each query requires a non-empty id")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"query {query_id}: prompt is empty")
        if query_id in seen_queries:
            raise ValueError(f"duplicate query id: {query_id}")
        seen_queries.add(query_id)

    for platform in platforms:
        if not isinstance(platform, dict):
            raise ValueError("each platform entry must be an object")
        platform_id = platform.get("id")
        surface = platform.get("surface")
        mode = platform.get("measurement_mode")
        priority = platform.get("priority")
        if not all(isinstance(v, str) and v.strip() for v in (platform_id, surface)):
            raise ValueError("each platform requires non-empty id and surface")
        if mode not in ALLOWED_MODES:
            raise ValueError(f"platform {platform_id}: invalid measurement_mode {mode!r}")
        if platform_id in seen_platforms:
            raise ValueError(f"duplicate platform id: {platform_id}")
        seen_platforms.add(platform_id)
        for query in queries:
            query_id = str(query["id"])
            prompt = str(query["query"])
            intent = str(query.get("intent") or query.get("cluster") or "unspecified")
            if query.get("brand_in_prompt") is False:
                lowered = prompt.casefold()
                if "аудио-реклама" in lowered or "audio-reclama" in lowered or "audio-reclama.ru" in lowered:
                    raise ValueError(f"generic prompt {query_id} contains a brand/domain hint")
            identity = "|".join((module_id, version, query_id, platform_id, str(mode)))
            queue_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
            notes = str(platform.get("note") or "")
            rows.append({
                "queue_id": queue_id,
                "module_id": module_id,
                "module_version": version,
                "query_id": query_id,
                "query": prompt,
                "intent": intent,
                **market,
                "platform": platform_id,
                "platform_surface": surface,
                "measurement_mode": str(mode),
                "platform_priority": str(priority if priority is not None else ""),
                "execution_status": PLANNED_STATUS,
                "region_verification": REGION_STATUS,
                "notes": notes,
            })
    return rows


def validate_rows(rows: list[dict[str, str]], expected: list[dict[str, str]] | None = None) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str, str]] = set()
    for line, row in enumerate(rows, start=2):
        prefix = f"line {line}"
        optional_fields = {"platform_priority", "notes"}
        missing = [field for field in QUEUE_FIELDS if field not in optional_fields and not (row.get(field) or "").strip()]
        if missing:
            errors.append(f"{prefix}: missing fields: {', '.join(missing)}")
            continue
        qid = row["queue_id"]
        if qid in seen_ids:
            errors.append(f"{prefix}: duplicate queue_id {qid}")
        seen_ids.add(qid)
        pair = (row["module_id"], row["query_id"], row["platform"])
        if pair in seen_pairs:
            errors.append(f"{prefix}: duplicate query/platform pair {pair}")
        seen_pairs.add(pair)
        if row["execution_status"] != PLANNED_STATUS:
            errors.append(f"{prefix}: planned queue status must remain {PLANNED_STATUS}")
        if row["region_verification"] not in {"UNVERIFIED", "VERIFIED", "BLOCKED", "NOT_APPLICABLE"}:
            errors.append(f"{prefix}: invalid region_verification")
        if row["measurement_mode"] not in ALLOWED_MODES:
            errors.append(f"{prefix}: invalid measurement_mode")
    if expected is not None:
        expected_pairs = {(r["module_id"], r["query_id"], r["platform"]) for r in expected}
        if seen_pairs != expected_pairs:
            missing = sorted(expected_pairs - seen_pairs)
            extra = sorted(seen_pairs - expected_pairs)
            if missing:
                errors.append(f"missing query/platform combinations: {missing[:10]}")
            if extra:
                errors.append(f"unexpected query/platform combinations: {extra[:10]}")
    return errors


def write_queue(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_queue(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != QUEUE_FIELDS:
            raise ValueError("queue CSV header does not match the AI visibility queue schema")
        return list(reader)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate", help="generate a planned queue from a frozen query module")
    generate.add_argument("--module", required=True, type=Path)
    generate.add_argument("--output", required=True, type=Path)
    validate = sub.add_parser("validate", help="validate queue structure and optional source-module coverage")
    validate.add_argument("--queue", required=True, type=Path)
    validate.add_argument("--module", type=Path, help="also verify the complete query × platform Cartesian product")
    args = parser.parse_args()

    try:
        if args.command == "generate":
            module = load_module(args.module)
            rows = build_rows(module)
            errors = validate_rows(rows, rows)
            if errors:
                raise ValueError("; ".join(errors))
            write_queue(rows, args.output)
            print(f"Generated {len(rows)} planned rows: {args.output}")
            print("All rows remain NOT_TESTED; region verification remains UNVERIFIED.")
            return 0

        rows = read_queue(args.queue)
        expected = build_rows(load_module(args.module)) if args.module else None
        errors = validate_rows(rows, expected)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"OK: {len(rows)} planned queue rows; no measurements were performed.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
