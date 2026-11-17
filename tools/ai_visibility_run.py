#!/usr/bin/env python3
"""Create and verify immutable, offline AI-visibility run passports."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLAN_SCHEMA = "studio/ai-visibility-run-passport/1"
RESULT_SCHEMA = "studio/ai-visibility-run-result/1"
QUEUE_REQUIRED = {
    "queue_id", "module_id", "module_version", "query_id", "query", "intent",
    "country_code", "interface_locale", "prompt_language", "answer_language",
    "platform", "platform_surface", "measurement_mode", "execution_status",
    "region_verification",
}
ALLOWED_MODES = {"consumer_ui", "model_api", "search_results_ui"}


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def file_entry(path: Path, base: Path, role: str) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"{path}: expected a regular file")
    try:
        stored_path = resolved.relative_to(base.resolve()).as_posix()
    except ValueError:
        stored_path = str(resolved)
    return {
        "role": role,
        "path": stored_path,
        "sha256": digest_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def resolve_entry(entry: dict[str, Any], manifest_path: Path) -> Path:
    raw = Path(entry["path"])
    return raw if raw.is_absolute() else (manifest_path.resolve().parent / raw).resolve()


def inspect_queue(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = set(reader.fieldnames or [])
        missing = sorted(QUEUE_REQUIRED - headers)
        if missing:
            raise ValueError(f"{path}: missing queue columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: queue is empty")
    identities = set()
    platforms = set()
    query_ids = set()
    markets = set()
    for line, row in enumerate(rows, start=2):
        if row.get("execution_status") != "NOT_TESTED":
            raise ValueError(f"{path}:{line}: planned queue row must remain NOT_TESTED")
        if row.get("measurement_mode") not in ALLOWED_MODES:
            raise ValueError(f"{path}:{line}: invalid measurement_mode")
        if row.get("region_verification") != "UNVERIFIED":
            raise ValueError(f"{path}:{line}: queue planner output must remain UNVERIFIED")
        identity = tuple(row.get(field, "") for field in (
            "query_id", "intent", "country_code", "interface_locale",
            "prompt_language", "answer_language", "platform", "platform_surface",
            "measurement_mode", "query",
        ))
        if identity in identities:
            raise ValueError(f"{path}:{line}: duplicate queue cell identity")
        identities.add(identity)
        platforms.add((row["platform"], row["platform_surface"], row["measurement_mode"]))
        query_ids.add(row["query_id"])
        markets.add((row["country_code"], row["interface_locale"], row["prompt_language"], row["answer_language"]))
    return {
        "planned_cells": len(rows),
        "query_count": len(query_ids),
        "platform_surface_count": len(platforms),
        "market_locale_count": len(markets),
        "measurement_modes": sorted({item[2] for item in platforms}),
        "region_verification_in_queue": "UNVERIFIED",
    }


def seal(payload: dict[str, Any], hash_field: str) -> dict[str, Any]:
    sealed = dict(payload)
    sealed.pop(hash_field, None)
    sealed[hash_field] = digest_bytes(canonical_bytes(sealed))
    return sealed


def verify_seal(payload: dict[str, Any], hash_field: str) -> bool:
    supplied = payload.get(hash_field)
    unsigned = dict(payload)
    unsigned.pop(hash_field, None)
    return isinstance(supplied, str) and supplied == digest_bytes(canonical_bytes(unsigned))


def create_plan(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output.resolve()
    base = output.parent
    if not args.module or not args.queue:
        raise ValueError("at least one --module and one --queue are required")
    modules = [file_entry(Path(item), base, "frozen_query_module") for item in args.module]
    queues = []
    for item in args.queue:
        path = Path(item).resolve(strict=True)
        summary = inspect_queue(path)
        entry = file_entry(path, base, "planned_execution_queue")
        entry["matrix"] = summary
        queues.append(entry)
    if args.region_status != "UNVERIFIED":
        raise ValueError("v1 run passports only accept UNVERIFIED region status; verified access requires a separately designed provenance workflow")
    evidence = None
    return seal({
        "schema": PLAN_SCHEMA,
        "run_id": args.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "lifecycle": "PLANNED",
        "scope": {
            "region_status": args.region_status,
            "region_label": None,
            "region_evidence": evidence,
            "operator_label": args.operator_label,
            "notes": args.notes,
        },
        "artifacts": {"query_modules": modules, "execution_queues": queues},
        "matrix_totals": {
            "planned_cells": sum(item["matrix"]["planned_cells"] for item in queues),
            "queue_files": len(queues),
            "query_module_files": len(modules),
        },
        "semantics": [
            "This passport freezes the planned experiment inputs; it is not an observation or visibility result.",
            "SHA-256 detects byte changes but does not authenticate the author or prove a region claim is true.",
            "Region status is an explicit operator attestation supported by a separately hashed evidence file when VERIFIED.",
            "Consumer UI, model API and search-results UI remain separate measurement modes.",
            "No AI/provider requests, paid checks, website changes or network measurements are performed."
        ],
    }, "passport_sha256")


def validate_plan(path: Path) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read passport: {exc}"], None
    if not isinstance(payload, dict):
        return ["passport root must be a JSON object"], None
    if payload.get("schema") != PLAN_SCHEMA:
        errors.append("unexpected passport schema")
    if not verify_seal(payload, "passport_sha256"):
        errors.append("passport_sha256 mismatch")
    if payload.get("lifecycle") != "PLANNED":
        errors.append("plan passport lifecycle must remain PLANNED")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return errors + ["artifacts must be an object"], payload
    entries = artifacts.get("query_modules", []) + artifacts.get("execution_queues", [])
    region_entry = (payload.get("scope") or {}).get("region_evidence")
    if region_entry:
        entries.append(region_entry)
    for entry in entries:
        try:
            artifact_path = resolve_entry(entry, path)
            if not artifact_path.is_file():
                errors.append(f"missing artifact: {entry.get('path')}")
            elif digest_file(artifact_path) != entry.get("sha256"):
                errors.append(f"SHA-256 mismatch: {entry.get('path')}")
            elif artifact_path.stat().st_size != entry.get("size_bytes"):
                errors.append(f"size mismatch: {entry.get('path')}")
        except (OSError, KeyError, TypeError) as exc:
            errors.append(f"invalid artifact entry: {exc}")
    return errors, payload


def create_result(args: argparse.Namespace) -> dict[str, Any]:
    errors, plan = validate_plan(args.passport)
    if errors or plan is None:
        raise ValueError("plan passport validation failed: " + "; ".join(errors))
    if args.run_id != plan.get("run_id"):
        raise ValueError("--run-id does not match the plan passport")
    base = args.output.resolve().parent
    csv_entry = file_entry(Path(args.observations_csv), base, "benchmark_observations_csv") if args.observations_csv else None
    records = []
    if args.evidence_dir:
        directory = Path(args.evidence_dir).resolve(strict=True)
        if not directory.is_dir():
            raise ValueError("--evidence-dir must be a directory")
        for record_path in sorted(directory.glob("*.json")):
            records.append(file_entry(record_path, base, "primary_observation_json"))
        if not records:
            raise ValueError("evidence directory contains no *.json records")
    if not csv_entry and not records:
        raise ValueError("provide --observations-csv and/or --evidence-dir")
    return seal({
        "schema": RESULT_SCHEMA,
        "run_id": args.run_id,
        "finalized_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "lifecycle": "FINALIZED",
        "plan_passport_sha256": plan["passport_sha256"],
        "observation_artifacts": {
            "benchmark_csv": csv_entry,
            "primary_json_records": records,
        },
        "semantics": [
            "This result passport links collected artifacts to the exact frozen plan passport.",
            "It records artifact integrity and linkage, not the truth or quality of the measured answers.",
            "Run the benchmark and evidence validators before finalization; this command does not replace them.",
            "A blocked or unavailable observation is not zero visibility."
        ],
    }, "result_sha256")


def validate_result(path: Path, plan_path: Path) -> list[str]:
    errors, plan = validate_plan(plan_path)
    if errors or plan is None:
        return ["plan passport invalid: " + "; ".join(errors)]
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read result passport: {exc}"]
    if not isinstance(result, dict):
        return ["result passport root must be a JSON object"]
    if result.get("schema") != RESULT_SCHEMA:
        errors.append("unexpected result passport schema")
    if not verify_seal(result, "result_sha256"):
        errors.append("result_sha256 mismatch")
    if result.get("lifecycle") != "FINALIZED":
        errors.append("result passport lifecycle must be FINALIZED")
    if result.get("run_id") != plan.get("run_id"):
        errors.append("result run_id does not match plan passport")
    if result.get("plan_passport_sha256") != plan.get("passport_sha256"):
        errors.append("result does not reference this exact plan passport")
    artifacts = result.get("observation_artifacts", {})
    entries = []
    if artifacts.get("benchmark_csv"):
        entries.append(artifacts["benchmark_csv"])
    entries.extend(artifacts.get("primary_json_records", []))
    if not entries:
        errors.append("result passport contains no observation artifacts")
    for entry in entries:
        try:
            artifact_path = resolve_entry(entry, path)
            if not artifact_path.is_file():
                errors.append(f"missing observation artifact: {entry.get('path')}")
            elif digest_file(artifact_path) != entry.get("sha256"):
                errors.append(f"SHA-256 mismatch: {entry.get('path')}")
            elif artifact_path.stat().st_size != entry.get("size_bytes"):
                errors.append(f"size mismatch: {entry.get('path')}")
        except (OSError, KeyError, TypeError) as exc:
            errors.append(f"invalid observation artifact entry: {exc}")
    return errors


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="freeze query modules and planned queues into a run passport")
    create.add_argument("--run-id", required=True)
    create.add_argument("--module", action="append", default=[])
    create.add_argument("--queue", action="append", default=[])
    create.add_argument("--output", required=True, type=Path)
    create.add_argument("--region-status", choices=("UNVERIFIED",), default="UNVERIFIED")
    create.add_argument("--operator-label")
    create.add_argument("--notes")
    validate = sub.add_parser("validate", help="verify plan passport seal and frozen input files")
    validate.add_argument("--passport", required=True, type=Path)
    finalize = sub.add_parser("finalize", help="freeze observation artifacts against the exact plan passport")
    finalize.add_argument("--passport", required=True, type=Path)
    finalize.add_argument("--run-id", required=True)
    finalize.add_argument("--observations-csv", type=Path)
    finalize.add_argument("--evidence-dir", type=Path)
    finalize.add_argument("--output", required=True, type=Path)
    validate_final = sub.add_parser("validate-final", help="verify final result and all referenced files")
    validate_final.add_argument("--passport", required=True, type=Path)
    validate_final.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            payload = create_plan(args)
            write_json(args.output, payload)
            print(f"PASS: created PLANNED passport {payload['passport_sha256']}")
        elif args.command == "validate":
            errors, payload = validate_plan(args.passport)
            if errors:
                raise ValueError("; ".join(errors))
            print(f"PASS: passport {payload['run_id']} and all frozen inputs verified")
        elif args.command == "finalize":
            payload = create_result(args)
            write_json(args.output, payload)
            print(f"PASS: finalized run {payload['run_id']} with result hash {payload['result_sha256']}")
        else:
            errors = validate_result(args.result, args.passport)
            if errors:
                raise ValueError("; ".join(errors))
            print("PASS: plan, result and all referenced observation artifacts verified")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
