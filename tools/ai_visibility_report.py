#!/usr/bin/env python3
"""Build a reproducible offline report from a validated AI-visibility run."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.ai_visibility_benchmark import summarize, validate as validate_benchmark
from tools.ai_visibility_coverage import analyze as analyze_coverage
from tools.ai_visibility_run import resolve_entry, validate_result

REPORT_SCHEMA = "studio/ai-visibility-final-report/1"


def build_report(passport_path: Path, result_path: Path) -> dict[str, Any]:
    validation_errors = validate_result(result_path, passport_path)
    if validation_errors:
        raise ValueError("run/result validation failed: " + "; ".join(validation_errors))
    plan = json.loads(passport_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    artifacts = result["observation_artifacts"]
    csv_path = resolve_entry(artifacts["benchmark_csv"], result_path)
    record_entries = artifacts["primary_json_records"]
    queue_entries = plan["artifacts"]["execution_queues"]
    queue_paths = [resolve_entry(entry, passport_path) for entry in queue_entries]

    benchmark_errors, rows = validate_benchmark(csv_path)
    if benchmark_errors:
        raise ValueError("benchmark CSV validation failed: " + "; ".join(benchmark_errors))
    coverage = analyze_coverage(queue_paths, csv_path)
    if coverage["errors"]:
        raise ValueError("coverage validation failed: " + "; ".join(coverage["errors"]))
    coverage["inputs"] = {
        "queue_files": [entry.get("path") for entry in queue_entries],
        "observation_file": csv_entry.get("path"),
    }
    benchmark = summarize(rows)

    region_attestation = (plan.get("scope") or {}).get("region_attestation")
    region_summary = {
        "status": (plan.get("scope") or {}).get("region_status", "UNVERIFIED"),
        "attestation_id": None,
        "attestation_sha256": region_attestation.get("sha256") if region_attestation else None,
    }
    if region_attestation:
        attestation_path = resolve_entry(region_attestation, passport_path)
        attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
        region_summary["attestation_id"] = attestation.get("attestation_id")

    return {
        "schema": REPORT_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "run": {
            "run_id": plan.get("run_id"),
            "lifecycle": result.get("lifecycle"),
            "plan_passport_sha256": plan.get("passport_sha256"),
            "result_passport_sha256": result.get("result_sha256"),
            "region": region_summary,
            "planned_cells": (plan.get("matrix_totals") or {}).get("planned_cells"),
            "queue_files": len(queue_entries),
            "primary_observation_records": len(record_entries),
        },
        "coverage": coverage,
        "benchmark": benchmark,
        "interpretation": [
            "Collection coverage measures whether planned cells have observations; it is not a visibility-success rate.",
            "Only OK and PARTIAL rows contribute to answered-only benchmark scores and observed discovery rates.",
            "Blocked, unavailable, unsupported, error and untested outcomes are not zero visibility.",
            "Consumer UI, model API and search-results UI are reported as separate measurement surfaces.",
            "This report is derived from a validated immutable run/result passport pair and does not independently establish the truth of captured answers.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    run = report["run"]
    coverage = report["coverage"]
    totals = coverage["totals"]
    lines = [
        "# AI Visibility Run Report",
        "",
        f"- Run ID: {run['run_id']}",
        f"- Region status: {run['region']['status']}",
        f"- Plan passport SHA-256: {run['plan_passport_sha256']}",
        f"- Result passport SHA-256: {run['result_passport_sha256']}",
        f"- Planned cells: {totals['planned_cells']}",
        f"- Observed cells: {totals['observed_cells']}",
        f"- Missing cells: {totals['missing_cells']}",
        f"- Collection coverage: {totals['coverage_pct']}%",
        f"- Primary JSON records: {run['primary_observation_records']}",
        "",
        "## Answer status counts",
        "",
        "| Status | Rows |",
        "|---|---:|",
    ]
    for status, count in coverage["answer_status_counts"].items():
        lines.append(f"| {status} | {count} |")
    lines.extend(["", "## Coverage by platform", "", "| Platform | Planned | Observed | Missing | Coverage |", "|---|---:|---:|---:|---:|"])
    for item in coverage["coverage"]["by_platform"]:
        lines.append(f"| {item['group']} | {item['planned_cells']} | {item['observed_cells']} | {item['missing_cells']} | {item['coverage_pct']}% |")
    lines.extend(["", "## Answered-only benchmark groups", "", "| Platform | Mode | Intent | Answered | Discovery observed | Discovery hits | Discovery rate | Critical errors |", "|---|---|---|---:|---:|---:|---:|---:|"])
    for group in report["benchmark"]["groups"]:
        rate = "—" if group["generic_discovery_rate"] is None else f"{group['generic_discovery_rate']:.1%}"
        lines.append(
            f"| {group['platform']} | {group['measurement_mode']} | {group['intent']} | "
            f"{group['answered']} | {group['generic_discovery_observed']} | "
            f"{group['generic_discovery_hits']} | {rate} | {group['critical_errors']} |"
        )
    lines.extend(["", "## Missing planned cells", ""])
    if coverage["missing_cells"]:
        lines.extend(["| Query ID | Platform | Mode | Intent |", "|---|---|---|---|"])
        for item in coverage["missing_cells"]:
            lines.append(f"| {item['query_id']} | {item['platform']} | {item['measurement_mode']} | {item['intent']} |")
    else:
        lines.append("None.")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in report["interpretation"])
    return "\n".join(lines) + "\n"


def write_outputs(report: dict[str, Any], json_path: Path | None, markdown_path: Path | None) -> None:
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passport", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.json_out and not args.markdown_out:
            raise ValueError("provide --json-out and/or --markdown-out")
        report = build_report(args.passport, args.result)
        write_outputs(report, args.json_out, args.markdown_out)
        print(f"PASS: report generated for validated run {report['run']['run_id']}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
