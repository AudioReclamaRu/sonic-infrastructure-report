#!/usr/bin/env python3
"""Validate experiment records and the mandatory six-discipline review.

Uses only the Python standard library. This is a focused release-contract
checker, not a full JSON Schema, ethics, legal, privacy or security audit.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "experiment-record.schema.json"
EXPERIMENT_DIR = ROOT / "research" / "experiments"

LENSES = (
    "semiotics",
    "ethology_behavior",
    "chronobiology",
    "ergonomics_human_factors",
    "complex_systems",
    "cryptology",
)
LENS_STATUSES = {"APPLICABLE", "NOT_APPLICABLE", "NOT_ASSESSED", "HOLD"}
RECORD_STATUSES = {
    "PROPOSED", "PLANNED", "RUNNING", "HOLD",
    "COMPLETED", "REPRODUCED", "FAILED",
}
EXECUTED_STATUSES = {"COMPLETED", "REPRODUCED", "FAILED"}
ID_RE = re.compile(r"^EXP-[A-Z0-9][A-Z0-9._-]{2,63}$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
HASH_LENGTHS = {"SHA-256": 64, "SHA-384": 96, "SHA-512": 128}


class DuplicateKeyError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
    )


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(record: Any, label: str = "<record>") -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{label}: top-level JSON value must be an object"]

    required = (
        "schema_version", "record_kind", "experiment_id", "status",
        "experiment_type", "protocol_version", "created_at", "owner",
        "question", "hypothesis", "null_hypothesis", "falsifier",
        "scope", "variables", "controls", "six_lenses",
        "data_provenance", "analysis_plan", "external_release",
    )
    for field in required:
        if field not in record:
            errors.append(f"{label}: missing required field: {field}")

    if record.get("schema_version") != "1.0":
        errors.append(f"{label}: schema_version must be '1.0'")
    if record.get("record_kind") != "experiment":
        errors.append(f"{label}: record_kind must be 'experiment'")
    experiment_id = record.get("experiment_id")
    if not isinstance(experiment_id, str) or not ID_RE.fullmatch(experiment_id):
        errors.append(f"{label}: experiment_id must match EXP-...")

    status = record.get("status")
    if status not in RECORD_STATUSES:
        errors.append(f"{label}: invalid status: {status!r}")

    for field in (
        "experiment_type", "protocol_version", "owner", "question",
        "hypothesis", "null_hypothesis", "falsifier", "scope", "analysis_plan",
    ):
        if not nonempty(record.get(field)):
            errors.append(f"{label}: {field} must be a non-empty string")

    created_at = record.get("created_at")
    if not isinstance(created_at, str) or not ISO_RE.fullmatch(created_at):
        errors.append(f"{label}: created_at must be offset-aware ISO 8601")

    variables = record.get("variables")
    if not isinstance(variables, list) or not variables:
        errors.append(f"{label}: variables must be a non-empty array")
    else:
        for index, variable in enumerate(variables):
            prefix = f"{label}: variables[{index}]"
            if not isinstance(variable, dict):
                errors.append(f"{prefix} must be an object")
                continue
            for field in ("name", "operational_definition", "unit", "measurement_method"):
                if not nonempty(variable.get(field)):
                    errors.append(f"{prefix}.{field} must be non-empty")
            if variable.get("role") not in {
                "independent", "dependent", "control", "confounder", "uncontrolled"
            }:
                errors.append(f"{prefix}.role has invalid value")

    if not isinstance(record.get("controls"), list) or any(
        not isinstance(item, str) for item in record.get("controls", [])
    ):
        errors.append(f"{label}: controls must be an array of strings")

    six = record.get("six_lenses")
    if not isinstance(six, dict):
        errors.append(f"{label}: six_lenses must be an object")
        six = {}
    else:
        missing = sorted(set(LENSES) - set(six))
        extra = sorted(set(six) - set(LENSES))
        for lens in missing:
            errors.append(f"{label}: missing six-lens review: {lens}")
        for lens in extra:
            errors.append(f"{label}: unknown six-lens key: {lens}")

    any_lens_hold = False
    any_lens_not_assessed = False
    for lens in LENSES:
        item = six.get(lens)
        if not isinstance(item, dict):
            continue
        prefix = f"{label}: six_lenses.{lens}"
        state = item.get("status")
        if state not in LENS_STATUSES:
            errors.append(f"{prefix}.status has invalid value: {state!r}")
            continue
        if not nonempty(item.get("risk")):
            errors.append(f"{prefix}.risk must be non-empty")
        if not nonempty(item.get("assessment")):
            errors.append(f"{prefix}.assessment must be non-empty")

        if state == "APPLICABLE":
            if not nonempty(item.get("check")):
                errors.append(f"{prefix}: APPLICABLE requires a concrete check")
            evidence = item.get("evidence")
            if not isinstance(evidence, list) or any(not isinstance(x, str) for x in evidence):
                errors.append(f"{prefix}: evidence must be an array of strings")
            elif status in EXECUTED_STATUSES and not any(nonempty(x) for x in evidence):
                errors.append(f"{prefix}: executed experiment requires evidence for APPLICABLE lens")
        elif state in {"NOT_APPLICABLE", "NOT_ASSESSED"}:
            if not nonempty(item.get("rationale")):
                errors.append(f"{prefix}: {state} requires a rationale")
            if state == "NOT_ASSESSED":
                any_lens_not_assessed = True
        elif state == "HOLD":
            any_lens_hold = True
            if not nonempty(item.get("hold_reason")):
                errors.append(f"{prefix}: HOLD requires hold_reason")

    if any_lens_hold and status != "HOLD":
        errors.append(f"{label}: any six-lens HOLD requires overall status HOLD")

    provenance = record.get("data_provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{label}: data_provenance must be an object")
        provenance = {}
    if not isinstance(provenance.get("sources"), list) or any(
        not isinstance(x, str) for x in provenance.get("sources", [])
    ):
        errors.append(f"{label}: data_provenance.sources must be an array of strings")
    elif status in EXECUTED_STATUSES and not any(nonempty(x) for x in provenance["sources"]):
        errors.append(f"{label}: executed experiment requires at least one provenance source")
    if not nonempty(provenance.get("collection_method")):
        errors.append(f"{label}: data_provenance.collection_method must be non-empty")
    if provenance.get("data_classification") not in {
        "public", "internal", "restricted", "sensitive"
    }:
        errors.append(f"{label}: invalid data_classification")

    hashes = provenance.get("hashes", [])
    if not isinstance(hashes, list):
        errors.append(f"{label}: data_provenance.hashes must be an array")
    else:
        for index, item in enumerate(hashes):
            prefix = f"{label}: data_provenance.hashes[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            algorithm = item.get("algorithm")
            if algorithm not in HASH_LENGTHS:
                errors.append(f"{prefix}.algorithm must be SHA-256, SHA-384 or SHA-512")
                continue
            digest = item.get("digest")
            if (
                not isinstance(digest, str)
                or len(digest) != HASH_LENGTHS[algorithm]
                or not re.fullmatch(r"[A-Fa-f0-9]+", digest)
            ):
                errors.append(f"{prefix}.digest has invalid length/format for {algorithm}")
            if not nonempty(item.get("object_ref")):
                errors.append(f"{prefix}.object_ref must be non-empty")

    if status in EXECUTED_STATUSES:
        for field in ("started_at", "completed_at"):
            value = record.get(field)
            if not isinstance(value, str) or not ISO_RE.fullmatch(value):
                errors.append(f"{label}: {status} requires offset-aware {field}")
        results = record.get("results")
        if not isinstance(results, dict):
            errors.append(f"{label}: {status} requires a results object")
        else:
            for field in ("run_id", "verdict"):
                if not nonempty(results.get(field)):
                    errors.append(f"{label}: results.{field} must be non-empty")
            if not isinstance(results.get("observations"), list):
                errors.append(f"{label}: results.observations must be an array")
            if not isinstance(results.get("measurements"), list):
                errors.append(f"{label}: results.measurements must be an array")
            if not isinstance(results.get("limitations"), list) or not results.get("limitations"):
                errors.append(f"{label}: results.limitations must be a non-empty array")
            if results.get("verdict") not in {
                "SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE", "CONTRADICTED"
            }:
                errors.append(f"{label}: invalid results.verdict")
        if any_lens_not_assessed:
            errors.append(f"{label}: completed/failed experiment cannot leave a lens NOT_ASSESSED")
        if any_lens_hold:
            errors.append(f"{label}: completed/failed experiment cannot contain a lens HOLD")

    if status == "HOLD" and not nonempty(record.get("hold_reason")):
        errors.append(f"{label}: overall HOLD requires hold_reason")

    if not isinstance(record.get("external_release"), bool):
        errors.append(f"{label}: external_release must be boolean")

    if record.get("external_release") is True:
        if status not in {"COMPLETED", "REPRODUCED"}:
            errors.append(f"{label}: external release requires COMPLETED or REPRODUCED")
        approval = record.get("release_approval")
        if not isinstance(approval, dict):
            errors.append(f"{label}: external release requires release_approval")
        else:
            for field in ("approved_by", "approved_at", "approval_ref"):
                if not nonempty(approval.get(field)):
                    errors.append(f"{label}: release_approval.{field} must be non-empty")
        if record.get("synthetic_fixture") is True:
            errors.append(f"{label}: synthetic fixture cannot be externally released")

    if record.get("synthetic_fixture") is not None and not isinstance(record.get("synthetic_fixture"), bool):
        errors.append(f"{label}: synthetic_fixture must be boolean when present")

    return errors


def main() -> int:
    if not SCHEMA.is_file():
        print(f"FAIL: missing schema: {SCHEMA.relative_to(ROOT)}")
        return 1
    if not EXPERIMENT_DIR.is_dir():
        print(f"FAIL: missing experiment directory: {EXPERIMENT_DIR.relative_to(ROOT)}")
        return 1

    try:
        schema = load_json(SCHEMA)
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        print(f"FAIL: cannot load experiment schema: {exc}")
        return 1

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        print("FAIL: experiment schema must declare JSON Schema draft 2020-12")
        return 1

    files = sorted(
        path for path in EXPERIMENT_DIR.rglob("*.json")
        if not path.name.endswith(".template.json")
    )
    if not files:
        print("OK: experiment schema and six-lens validator are present; no experiment records have been registered yet.")
        return 0

    failures: list[str] = []
    for path in files:
        relative = str(path.relative_to(ROOT))
        try:
            record = load_json(path)
        except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
            failures.append(f"{relative}: cannot parse JSON: {exc}")
            continue
        failures.extend(validate_record(record, relative))

    if failures:
        print("EXPERIMENT RECORD GATE: FAIL")
        for error in failures:
            print(f" - {error}")
        return 1

    print(f"EXPERIMENT RECORD GATE: PASS — {len(files)} experiment record(s), all six lenses checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
