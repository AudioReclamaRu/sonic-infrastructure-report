#!/usr/bin/env python3
"""Offline coverage-gap analysis for planned AI-visibility queues and observations.

This tool reads local CSV files only. It never performs measurements, calls providers,
infers geographic access, or treats blocked/no-answer observations as zero visibility.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

QUEUE_REQUIRED = {
    "queue_id", "module_id", "module_version", "query_id", "intent",
    "country_code", "interface_locale", "prompt_language", "answer_language",
    "platform", "platform_surface", "measurement_mode", "execution_status",
    "region_verification",
}
OBSERVATION_REQUIRED = {
    "run_id", "country_code", "interface_locale", "prompt_language",
    "answer_language", "platform", "platform_surface", "measurement_mode",
    "intent", "query_id", "answer_status", "observation_id",
}
ANSWERED = {"OK", "PARTIAL"}
NON_ANSWERED = {
    "NOT_TESTED", "NOT_AVAILABLE_IN_COUNTRY", "BLOCKED_REGION",
    "BLOCKED_AUTH", "UNSUPPORTED_PROVIDER", "BLOCKED_NETWORK", "ERROR",
}
VALID_STATUSES = ANSWERED | NON_ANSWERED


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: missing CSV header")
        return list(reader.fieldnames), list(reader)


def cell_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple((row.get(k) or "").strip() for k in (
        "query_id", "platform", "measurement_mode", "country_code", "interface_locale"
    ))


def dimension_key(row: dict[str, str], fields: tuple[str, ...]) -> str:
    return " / ".join((row.get(field) or "UNSPECIFIED").strip() or "UNSPECIFIED" for field in fields)


def analyze(queue_paths: list[Path], observation_path: Path | None = None) -> dict[str, Any]:
    planned: list[dict[str, str]] = []
    errors: list[str] = []
    for path in queue_paths:
        headers, rows = read_csv(path)
        missing = sorted(QUEUE_REQUIRED - set(headers))
        if missing:
            errors.append(f"{path}: missing queue columns: {', '.join(missing)}")
            continue
        for number, row in enumerate(rows, start=2):
            if row.get("execution_status") != "NOT_TESTED":
                errors.append(f"{path}:{number}: planned queue row must remain NOT_TESTED")
            if row.get("region_verification") not in {"UNVERIFIED", "VERIFIED", "BLOCKED", "NOT_APPLICABLE"}:
                errors.append(f"{path}:{number}: invalid region_verification")
            if not all((row.get(field) or "").strip() for field in QUEUE_REQUIRED):
                errors.append(f"{path}:{number}: blank required queue field")
            planned.append(row)

    plan_by_key: dict[tuple[str, ...], dict[str, str]] = {}
    for row in planned:
        key = cell_key(row)
        if key in plan_by_key:
            errors.append(f"duplicate planned cell: {key}")
        else:
            plan_by_key[key] = row

    observations: list[dict[str, str]] = []
    if observation_path is not None:
        headers, observations = read_csv(observation_path)
        missing = sorted(OBSERVATION_REQUIRED - set(headers))
        if missing:
            errors.append(f"{observation_path}: missing observation columns: {', '.join(missing)}")
            observations = []
        seen_ids: set[str] = set()
        for number, row in enumerate(observations, start=2):
            status = (row.get("answer_status") or "").strip().upper()
            if status not in VALID_STATUSES:
                errors.append(f"{observation_path}:{number}: unknown answer_status {status!r}")
            observation_id = (row.get("observation_id") or "").strip()
            if not observation_id:
                errors.append(f"{observation_path}:{number}: missing observation_id")
            elif observation_id in seen_ids:
                errors.append(f"{observation_path}:{number}: duplicate observation_id {observation_id}")
            seen_ids.add(observation_id)
            key = cell_key(row)
            if key not in plan_by_key:
                errors.append(f"{observation_path}:{number}: observation has no matching planned cell: {key}")

    observed_keys = {cell_key(row) for row in observations if cell_key(row) in plan_by_key}
    missing_keys = sorted(set(plan_by_key) - observed_keys)
    unexpected_count = sum(1 for error in errors if "no matching planned cell" in error)

    def aggregate(fields: tuple[str, ...]) -> list[dict[str, Any]]:
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in planned:
            groups[dimension_key(row, fields)].append(row)
        result = []
        for name, group in sorted(groups.items()):
            keys = {cell_key(row) for row in group}
            covered = keys & observed_keys
            result.append({
                "group": name,
                "planned_cells": len(keys),
                "observed_cells": len(covered),
                "missing_cells": len(keys - covered),
                "coverage_pct": round(100 * len(covered) / len(keys), 2) if keys else None,
            })
        return result

    status_counts = Counter((row.get("answer_status") or "").strip().upper() for row in observations)
    planned_regions = Counter((row.get("region_verification") or "UNSPECIFIED").strip() for row in planned)
    return {
        "schema": "ai-visibility/coverage-report/1",
        "inputs": {"queue_files": [str(p) for p in queue_paths],
                   "observation_file": str(observation_path) if observation_path else None},
        "totals": {
            "planned_cells": len(plan_by_key),
            "observed_cells": len(observed_keys),
            "missing_cells": len(missing_keys),
            "coverage_pct": round(100 * len(observed_keys) / len(plan_by_key), 2) if plan_by_key else None,
            "observation_rows": len(observations),
            "answered_rows": sum(status_counts[s] for s in ANSWERED),
            "non_answer_rows": sum(status_counts[s] for s in NON_ANSWERED),
            "unexpected_observation_rows": unexpected_count,
        },
        "answer_status_counts": dict(sorted(status_counts.items())),
        "region_verification_counts": dict(sorted(planned_regions.items())),
        "coverage": {
            "by_market": aggregate(("country_code", "interface_locale")),
            "by_platform": aggregate(("platform",)),
            "by_measurement_mode": aggregate(("measurement_mode",)),
            "by_intent": aggregate(("intent",)),
        },
        "missing_cells": [
            {"query_id": plan_by_key[key]["query_id"], "platform": plan_by_key[key]["platform"],
             "measurement_mode": plan_by_key[key]["measurement_mode"],
             "country_code": plan_by_key[key]["country_code"],
             "interface_locale": plan_by_key[key]["interface_locale"],
             "intent": plan_by_key[key]["intent"]}
            for key in missing_keys
        ],
        "errors": errors,
        "interpretation": [
            "Queue rows are planned cells, not observations.",
            "Coverage means a matching observation row exists; it does not mean visibility was achieved.",
            "BLOCKED, ERROR, unsupported and other non-answer statuses count as collection coverage, never as zero visibility.",
            "Visibility rates require answered observations only and are not calculated by this report.",
            "Region verification is reported from queue metadata and is not inferred from the machine running this tool."
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    totals = report["totals"]
    lines = [
        "# AI Visibility Coverage Report", "",
        f"- Planned cells: {totals['planned_cells']}",
        f"- Cells with observations: {totals['observed_cells']}",
        f"- Missing cells: {totals['missing_cells']}",
        f"- Collection coverage: {totals['coverage_pct']}%",
        f"- Observation rows: {totals['observation_rows']}",
        f"- Answered rows (OK/PARTIAL): {totals['answered_rows']}",
        f"- Non-answer rows: {totals['non_answer_rows']}",
        f"- Unexpected observation rows: {totals['unexpected_observation_rows']}", "",
    ]
    for heading, key in (
        ("By market and locale", "by_market"), ("By platform", "by_platform"),
        ("By measurement mode", "by_measurement_mode"), ("By intent", "by_intent"),
    ):
        lines.extend([f"## {heading}", "", "| Group | Planned | Observed | Missing | Coverage |",
                      "|---|---:|---:|---:|---:|"])
        for row in report["coverage"][key]:
            lines.append(f"| {row['group']} | {row['planned_cells']} | {row['observed_cells']} | {row['missing_cells']} | {row['coverage_pct']}% |")
        lines.append("")
    lines.extend(["## Missing planned cells", ""])
    if report["missing_cells"]:
        lines.extend(["| Query | Platform | Mode | Intent |", "|---|---|---|---|"])
        for row in report["missing_cells"]:
            lines.append(f"| {row['query_id']} | {row['platform']} | {row['measurement_mode']} | {row['intent']} |")
    else:
        lines.append("None.")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in report["interpretation"])
    if report["errors"]:
        lines.extend(["", "## Validation errors", ""])
        lines.extend(f"- {item}" for item in report["errors"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", action="append", required=True, type=Path,
                        help="planned queue CSV; repeat for multiple modules")
    parser.add_argument("--observations", type=Path,
                        help="benchmark observation CSV; omit for plan-only coverage")
    parser.add_argument("--json-out", type=Path, help="write machine-readable JSON report")
    parser.add_argument("--markdown-out", type=Path, help="write Markdown report")
    args = parser.parse_args(argv)
    try:
        report = analyze(args.queue, args.observations)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        markdown = render_markdown(report)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(payload, encoding="utf-8")
        if args.markdown_out:
            args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_out.write_text(markdown, encoding="utf-8")
        if not args.json_out and not args.markdown_out:
            print(markdown, end="")
        if report["errors"]:
            for error in report["errors"]:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
