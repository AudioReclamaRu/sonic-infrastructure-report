#!/usr/bin/env python3
"""Prepare a manual capture packet from a verified, frozen AI-visibility run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.ai_visibility_run import resolve_entry, validate_plan

PACKET_SCHEMA = "studio/ai-visibility-capture-packet/1"
CSV_FIELDS = [
    "run_id", "date_utc", "date_time_utc", "country_code", "region",
    "interface_locale", "prompt_language", "answer_language", "platform",
    "product_or_model", "platform_surface", "measurement_mode", "mode",
    "search_mode", "grounding_state", "language", "auth_status", "query_id",
    "intent", "query", "answer_status", "completeness_status",
    "brand_identity_score", "official_route_score", "service_or_answer_score",
    "commercial_accuracy_score", "expertise_retrieval_score", "source_quality_score",
    "citation_quality_score", "git_knowledge_score", "generic_discovery_hit",
    "critical_error", "cited_urls", "repository_file_cited", "competitors_mentioned",
    "answer_excerpt", "limitations", "operator_notes", "observation_id",
]


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return cleaned[:100] or "capture"


def read_queue(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {
            "queue_id", "query_id", "query", "intent", "country_code",
            "interface_locale", "prompt_language", "answer_language",
            "platform", "platform_surface", "measurement_mode",
            "execution_status", "region_verification",
        }
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"{path}: missing queue fields: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: queue contains no planned cells")
    for line, row in enumerate(rows, start=2):
        if row.get("execution_status") != "NOT_TESTED":
            raise ValueError(f"{path}:{line}: queue row is not in NOT_TESTED state")
        if row.get("region_verification") != "VERIFIED":
            raise ValueError(f"{path}:{line}: capture packets require VERIFIED regional scope")
    return rows


def build_packet(passport_path: Path, output_dir: Path) -> dict[str, Any]:
    errors, plan = validate_plan(passport_path)
    if errors or plan is None:
        raise ValueError("plan passport validation failed: " + "; ".join(errors))
    scope = plan.get("scope") or {}
    if scope.get("region_status") != "VERIFIED" or not scope.get("region_attestation"):
        raise ValueError("capture packet requires a VERIFIED regional run passport")
    if output_dir.exists():
        raise ValueError(f"output directory already exists; refusing to overwrite: {output_dir}")
    region_entry = scope["region_attestation"]
    attestation_path = resolve_entry(region_entry, passport_path)
    attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    attestation_id = attestation.get("attestation_id")
    if not attestation_id:
        raise ValueError("verified region attestation has no attestation_id")
    attestation_sha = region_entry.get("sha256")
    if digest_file(attestation_path) != attestation_sha:
        raise ValueError("region attestation SHA-256 no longer matches the plan passport")

    queue_entries = plan["artifacts"]["execution_queues"]
    rows: list[dict[str, str]] = []
    for entry in queue_entries:
        queue_path = resolve_entry(entry, passport_path)
        if digest_file(queue_path) != entry.get("sha256"):
            raise ValueError(f"queue SHA-256 no longer matches the plan passport: {entry.get('path')}")
        rows.extend(read_queue(queue_path))
    if len(rows) != (plan.get("matrix_totals") or {}).get("planned_cells"):
        raise ValueError("queue row count does not match passport planned_cells")
    if len({row["queue_id"] for row in rows}) != len(rows):
        raise ValueError("queue_id values must be unique across all queues")

    template_names = [safe_name("OBS-" + safe_name(row["queue_id"])) + ".json" for row in rows]
    if len(set(template_names)) != len(template_names):
        raise ValueError("queue IDs collide after safe filename normalization")
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    csv_path = output_dir / "capture.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "run_id": plan["run_id"],
                "country_code": row["country_code"],
                "interface_locale": row["interface_locale"],
                "prompt_language": row["prompt_language"],
                "answer_language": row["answer_language"],
                "platform": row["platform"],
                "platform_surface": row["platform_surface"],
                "measurement_mode": row["measurement_mode"],
                "query_id": row["query_id"],
                "intent": row["intent"],
                "query": row["query"],
                "answer_status": "NOT_TESTED",
                "completeness_status": "NOT_TESTED",
            })

    template_files = []
    for index, row in enumerate(rows):
        observation_id = "OBS-" + safe_name(row["queue_id"])
        record = {
            "schema": "studio/ai-visibility-observation/1",
            "observation_id": observation_id,
            "run_id": plan["run_id"],
            "observed_at_utc": "",
            "market": {
                "country_code": row["country_code"],
                "region": "",
                "region_evidence": "",
                "interface_locale": row["interface_locale"],
                "prompt_language": row["prompt_language"],
                "answer_language": row["answer_language"],
                "region_attestation_id": attestation_id,
                "region_attestation_sha256": attestation_sha,
            },
            "platform": {
                "id": row["platform"],
                "product": "",
                "surface": row["platform_surface"],
                "measurement_mode": row["measurement_mode"],
            },
            "query": {
                "query_id": row["query_id"],
                "intent": row["intent"],
                "exact_prompt": row["query"],
            },
            "answer_status": "NOT_TESTED",
            "raw_answer": "",
            "answer_excerpt": "",
            "named_providers": [],
            "generic_discovery_hit": None,
            "critical_error": None,
            "scores": {
                "brand_identity": None, "official_route": None,
                "service_or_answer": None, "commercial_accuracy": None,
                "expertise_retrieval": None, "source_quality": None,
                "citation_quality": None, "git_knowledge": None,
            },
            "evidence": {"sources": [], "repository_files": [], "capture_artifact": None},
            "limitations": [],
            "operator_notes": "DRAFT TEMPLATE — replace placeholders only from an actual captured session.",
        }
        filename = template_names[index]
        (evidence_dir / filename).write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        template_files.append(f"evidence/{filename}")

    manifest = {
        "schema": PACKET_SCHEMA,
        "packet_status": "DRAFT_TEMPLATES_ONLY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "run_id": plan["run_id"],
        "plan_passport_sha256": plan["passport_sha256"],
        "region_attestation_id": attestation_id,
        "region_attestation_sha256": attestation_sha,
        "planned_cells": len(rows),
        "queue_files": [
            {"path": entry["path"], "sha256": entry["sha256"]}
            for entry in queue_entries
        ],
        "capture_csv": "capture.csv",
        "evidence_templates": template_files,
        "semantics": [
            "This packet contains blank capture templates, not observations or evidence.",
            "Empty observed_at_utc, region, region_evidence and platform.product fields must be completed from a real session.",
            "NOT_TESTED means no measurement has yet been recorded.",
            "A verified regional session is time-bound; every observation must be within 30 minutes of the session capture.",
        ],
    }
    (output_dir / "capture-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    instructions = f"""# Manual AI Visibility Capture Packet

**DRAFT TEMPLATES ONLY — no AI responses have been collected.**

- Run ID: {plan['run_id']}
- Planned cells: {len(rows)}
- Region attestation: {attestation_id}
- Plan passport SHA-256: {plan['passport_sha256']}

## Before collection

1. Confirm that the exact product, consumer interface and measurement mode match the queue row.
2. Use the real direct Russian network session represented by the reviewed regional attestation. Do not use VPN, proxy, cloud host or remote desktop.
3. The regional session and every observation must be within the same 30-minute window. If that window expires, stop and create a new attestation and a new run passport.
4. Keep consumer UI, model API and search-results UI observations separate.

## Complete each JSON template

For each file in evidence/:

- Set observed_at_utc to the actual capture time in ISO-8601 UTC.
- Fill market.region and market.region_evidence with the real region and the exact evidence supporting it.
- Fill platform.product with the exact product/model shown in the session.
- Set answer_status from the observed outcome; never convert a block or unavailable state into an empty successful answer.
- For OK/PARTIAL, preserve the complete raw answer, answer excerpt, sources, capture artifact reference and all applicable scores.
- For non-answer statuses, keep raw_answer empty, all scores null, and discovery/error flags null.
- Keep the preassigned observation_id and run_id unchanged.

## Complete capture.csv

Fill date_utc/date_time_utc, product_or_model, completeness_status, status, observation_id and the remaining benchmark fields from the same captured session. Each answered CSV row must link to its exact JSON file.

## Validate and finalize

Run the evidence batch validator with every frozen queue and the exact region attestation, then run benchmark validation, run finalization and validate-final. The final report is generated only after those gates pass.

Do not invent timestamps, answers, citations, regional evidence or scores. These files are working templates and are not valid observation records until completed from real captures.
"""
    (output_dir / "README_CAPTURE.md").write_text(instructions, encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passport", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = build_packet(args.passport, args.output_dir)
        print(f"PASS: prepared {manifest['planned_cells']} draft capture templates for run {manifest['run_id']}")
        print("No measurements or observations were created.")
        return 0
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
