#!/usr/bin/env python3
"""Offline validator and summarizer for manual AI-visibility benchmark CSV."""
from __future__ import annotations
import argparse, csv, json, math, sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCORE_FIELDS = (
    "brand_identity_score", "official_route_score", "service_or_answer_score",
    "commercial_accuracy_score", "expertise_retrieval_score",
    "source_quality_score", "citation_quality_score", "git_knowledge_score",
)
REQUIRED_FIELDS = (
    "run_id", "date_utc", "country_code", "interface_locale",
    "prompt_language", "answer_language", "platform", "platform_surface",
    "measurement_mode", "intent", "query_id", "query", "answer_status",
    "completeness_status",
)
ANSWERED = {"OK", "PARTIAL"}
NON_ANSWERED = {
    "NOT_TESTED", "NOT_AVAILABLE_IN_COUNTRY", "BLOCKED_REGION",
    "BLOCKED_AUTH", "UNSUPPORTED_PROVIDER", "BLOCKED_NETWORK", "ERROR",
}
VALID_STATUSES = ANSWERED | NON_ANSWERED
VALID_MODES = {"consumer_ui", "model_api", "search_results_ui"}
VALID_BOOL = {"true", "false", "1", "0", "yes", "no"}
GROUP_FIELDS = (
    "run_id", "country_code", "interface_locale", "prompt_language",
    "platform", "platform_surface", "measurement_mode", "intent",
)

def read_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")
        return list(reader.fieldnames), list(reader)

def validate(path: Path):
    headers, rows = read_rows(path)
    errors = []
    missing = [field for field in REQUIRED_FIELDS if field not in headers]
    if missing:
        return [f"missing required columns: {', '.join(missing)}"], rows
    seen = set()
    for line, row in enumerate(rows, start=2):
        prefix = f"line {line}"
        for field in REQUIRED_FIELDS:
            if not (row.get(field) or "").strip():
                errors.append(f"{prefix}: {field} is required")
        status = (row.get("answer_status") or "").strip().upper()
        if status and status not in VALID_STATUSES:
            errors.append(f"{prefix}: unknown answer_status {status!r}")
        mode = (row.get("measurement_mode") or "").strip().lower()
        if mode and mode not in VALID_MODES:
            errors.append(f"{prefix}: measurement_mode must be one of {sorted(VALID_MODES)}")
        for field in SCORE_FIELDS:
            raw = (row.get(field) or "").strip()
            if not raw:
                continue
            try:
                value = float(raw)
            except ValueError:
                errors.append(f"{prefix}: {field} must be blank or an integer from 0 to 2")
                continue
            if not math.isfinite(value) or value < 0 or value > 2 or not value.is_integer():
                errors.append(f"{prefix}: {field} must be blank or an integer from 0 to 2")
        hit = (row.get("generic_discovery_hit") or "").strip().lower()
        if hit and hit not in VALID_BOOL:
            errors.append(f"{prefix}: generic_discovery_hit must be blank or boolean")
        if status in NON_ANSWERED:
            populated = [f for f in SCORE_FIELDS if (row.get(f) or "").strip()]
            if populated:
                errors.append(f"{prefix}: non-answer status {status} cannot carry scores: " + ", ".join(populated))
            if hit:
                errors.append(f"{prefix}: non-answer status {status} cannot carry generic_discovery_hit")
        key_fields = (
            "run_id", "country_code", "interface_locale", "prompt_language",
            "platform", "platform_surface", "measurement_mode", "intent", "query_id",
        )
        key = tuple((row.get(field) or "").strip() for field in key_fields)
        if all(key):
            if key in seen:
                errors.append(f"{prefix}: duplicate observation key {key}")
            seen.add(key)
    return errors, rows

def truth(value):
    value = (value or "").strip().lower()
    if not value:
        return None
    return value in {"true", "1", "yes"}

def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    buckets = defaultdict(list)
    for row in rows:
        buckets[tuple((row.get(field) or "").strip() for field in GROUP_FIELDS)].append(row)
    output = []
    for key, group in sorted(buckets.items()):
        answered = [r for r in group if (r.get("answer_status") or "").strip().upper() in ANSWERED]
        scores = {}
        for field in SCORE_FIELDS:
            values = [float(r[field]) for r in answered if (r.get(field) or "").strip()]
            scores[field] = round(sum(values) / len(values), 3) if values else None
        hits = [truth(r.get("generic_discovery_hit", "")) for r in answered]
        known_hits = [v for v in hits if v is not None]
        critical = sum(1 for r in answered if (r.get("critical_error") or "").strip())
        output.append({
            **dict(zip(GROUP_FIELDS, key)),
            "observations": len(group),
            "answered": len(answered),
            "not_answered": len(group) - len(answered),
            "generic_discovery_observed": len(known_hits),
            "generic_discovery_hits": sum(1 for v in known_hits if v),
            "generic_discovery_rate": round(sum(1 for v in known_hits if v) / len(known_hits), 3) if known_hits else None,
            "critical_errors": critical,
            "critical_error_rate": round(critical / len(answered), 3) if answered else None,
            "mean_scores": scores,
        })
    return {
        "schema": "studio/ai-visibility-benchmark-summary/1",
        "grouping": list(GROUP_FIELDS),
        "answer_statuses_counted_as_answered": sorted(ANSWERED),
        "note": "Rates use explicitly observed answered rows only. Blocked, unavailable, unsupported and untested rows are not zero visibility. Consumer UI, model API and search-results UI remain separate.",
        "groups": output,
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate", help="validate benchmark CSV structure and rows")
    check.add_argument("csv_file", type=Path)
    report = sub.add_parser("summarize", help="validate and write grouped JSON summary")
    report.add_argument("csv_file", type=Path)
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        errors, rows = validate(args.csv_file)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("Benchmark CSV validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    if args.command == "validate":
        print(f"PASS: {len(rows)} observation row(s); no network or paid checks were used.")
        return 0
    result = summarize(rows)
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"ERROR writing summary: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: summarized {len(rows)} observation row(s) into {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
