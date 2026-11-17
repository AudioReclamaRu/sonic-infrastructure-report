#!/usr/bin/env python3
"""Audit a portable AI-visibility run package without performing measurements."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from tools.ai_visibility_region import validate_attestation
from tools.ai_visibility_run import validate_plan

PACKAGE_SCHEMA = "studio/ai-visibility-run-package/1"
PACKET_SCHEMA = "studio/ai-visibility-capture-packet/1"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _package_file(root: Path, relative: object, label: str, *, directory: bool = False) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"{label}: package-relative path is required")
    candidate = Path(relative)
    if candidate.is_absolute() or "\\" in relative or ".." in candidate.parts or "." in candidate.parts:
        raise ValueError(f"{label}: unsafe package-relative path: {relative}")
    resolved = (root / candidate).resolve(strict=True)
    try:
        resolved.relative_to(root.resolve(strict=True))
    except ValueError as exc:
        raise ValueError(f"{label}: path escapes package root: {relative}") from exc
    if directory:
        if not resolved.is_dir():
            raise ValueError(f"{label}: expected a directory: {relative}")
    elif not resolved.is_file():
        raise ValueError(f"{label}: expected a regular file: {relative}")
    return resolved


def _check_hash(root: Path, entry: object, label: str) -> Path:
    if not isinstance(entry, dict):
        raise ValueError(f"{label}: manifest entry must be an object")
    path = _package_file(root, entry.get("path"), label)
    if _digest(path) != entry.get("sha256"):
        raise ValueError(f"{label}: SHA-256 mismatch")
    return path


def validate_package(manifest_path: Path) -> tuple[list[str], dict[str, Any] | None]:
    """Validate package layout, all frozen inputs, passport, attestation and blank packet."""
    try:
        root = manifest_path.resolve(strict=True).parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read package manifest: {exc}"], None
    if not isinstance(manifest, dict):
        return ["package manifest root must be an object"], None

    errors: list[str] = []
    if manifest.get("schema") != PACKAGE_SCHEMA:
        errors.append("unexpected package schema")
    if manifest.get("package_status") != "PLANNED_CAPTURE_READY":
        errors.append("package status must remain PLANNED_CAPTURE_READY")
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        errors.append("run_id must be a non-empty string")
    try:
        module_path = _check_hash(root, manifest.get("query_module"), "query_module")
        queue_path = _check_hash(root, manifest.get("queue"), "queue")
        attestation_path = _check_hash(root, manifest.get("region_attestation"), "region_attestation")
        passport_path = _check_hash(root, manifest.get("plan_passport"), "plan_passport")
    except (OSError, ValueError, TypeError) as exc:
        return errors + [str(exc)], manifest

    if manifest["region_attestation"].get("attestation_id") is None:
        errors.append("region_attestation.attestation_id is required")
    try:
        attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
        attestation_errors, attestation_status = validate_attestation(attestation, attestation_path.parent)
        if attestation_errors or attestation_status != "VERIFIED":
            errors.append("regional attestation is not VERIFIED: " + "; ".join(attestation_errors or [attestation_status]))
        if attestation.get("attestation_id") != manifest["region_attestation"].get("attestation_id"):
            errors.append("manifest region attestation ID does not match attestation")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"cannot validate regional attestation: {exc}")

    plan_errors, plan = validate_plan(passport_path)
    if plan_errors or plan is None:
        errors.append("plan passport invalid: " + "; ".join(plan_errors))
    else:
        if plan.get("run_id") != run_id:
            errors.append("plan run_id does not match package manifest")
        if plan.get("passport_sha256") != manifest["plan_passport"].get("sha256"):
            errors.append("plan passport hash does not match package manifest")
        scope = plan.get("scope") or {}
        region_entry = scope.get("region_attestation") or {}
        if region_entry.get("sha256") != manifest["region_attestation"].get("sha256"):
            errors.append("plan passport is not bound to the packaged regional attestation")
        artifacts = plan.get("artifacts") or {}
        modules = artifacts.get("query_modules") or []
        queues = artifacts.get("execution_queues") or []
        if len(modules) != 1 or modules[0].get("sha256") != manifest["query_module"].get("sha256"):
            errors.append("plan passport is not bound to the packaged query module")
        if len(queues) != 1 or queues[0].get("sha256") != manifest["queue"].get("sha256"):
            errors.append("plan passport is not bound to the packaged queue")

    try:
        with queue_path.open("r", encoding="utf-8-sig", newline="") as stream:
            queue_rows = list(csv.DictReader(stream))
        planned_cells = manifest["queue"].get("planned_cells")
        if len(queue_rows) != planned_cells:
            errors.append("queue row count does not match package manifest planned_cells")
        if any(row.get("execution_status") != "NOT_TESTED" for row in queue_rows):
            errors.append("package queue contains a row not marked NOT_TESTED")
    except (OSError, TypeError) as exc:
        errors.append(f"cannot inspect package queue: {exc}")

    try:
        capture_dir = _package_file(root, manifest.get("capture_packet", {}).get("path"), "capture_packet", directory=True)
    except (OSError, ValueError, AttributeError) as exc:
        errors.append(str(exc))
        return errors, manifest

    packet_manifest_path = capture_dir / "capture-manifest.json"
    try:
        packet = json.loads(packet_manifest_path.read_text(encoding="utf-8"))
        if packet.get("schema") != PACKET_SCHEMA:
            errors.append("unexpected capture packet schema")
        if packet.get("packet_status") != "DRAFT_TEMPLATES_ONLY":
            errors.append("capture packet must remain DRAFT_TEMPLATES_ONLY")
        if packet.get("run_id") != run_id:
            errors.append("capture packet run_id does not match package")
        if packet.get("plan_passport_sha256") != manifest["plan_passport"].get("sha256"):
            errors.append("capture packet is not bound to this plan passport")
        if packet.get("region_attestation_id") != manifest["region_attestation"].get("attestation_id"):
            errors.append("capture packet region attestation ID does not match package")
        if packet.get("region_attestation_sha256") != manifest["region_attestation"].get("sha256"):
            errors.append("capture packet region attestation hash does not match package")
        if packet.get("planned_cells") != manifest["queue"].get("planned_cells"):
            errors.append("capture packet planned_cells does not match queue")
        csv_path = _package_file(capture_dir, packet.get("capture_csv"), "capture_csv")
        with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            capture_rows = list(csv.DictReader(stream))
        if len(capture_rows) != packet.get("planned_cells"):
            errors.append("capture CSV row count does not match capture packet")
        for row in capture_rows:
            if row.get("run_id") != run_id or row.get("answer_status") != "NOT_TESTED" or row.get("completeness_status") != "NOT_TESTED":
                errors.append("capture CSV contains completed or foreign-run rows")
                break
        templates = packet.get("evidence_templates")
        if not isinstance(templates, list) or len(templates) != packet.get("planned_cells"):
            errors.append("evidence template list does not match planned_cells")
        else:
            seen_ids: set[str] = set()
            for relative in templates:
                template_path = _package_file(capture_dir, relative, "evidence_template")
                record = json.loads(template_path.read_text(encoding="utf-8"))
                if record.get("run_id") != run_id or record.get("answer_status") != "NOT_TESTED":
                    errors.append(f"template is not a NOT_TESTED record for this run: {relative}")
                if record.get("observed_at_utc") or record.get("raw_answer"):
                    errors.append(f"draft template contains observation data: {relative}")
                if (record.get("platform") or {}).get("product"):
                    errors.append(f"draft template contains a platform product: {relative}")
                market = record.get("market") or {}
                if market.get("region") or market.get("region_evidence"):
                    errors.append(f"draft template contains regional observation data: {relative}")
                scores = record.get("scores") or {}
                if any(value is not None for value in scores.values()):
                    errors.append(f"draft template contains scores: {relative}")
                observation_id = record.get("observation_id")
                if not isinstance(observation_id, str) or observation_id in seen_ids:
                    errors.append(f"missing or duplicate observation_id in template: {relative}")
                seen_ids.add(observation_id)
        _package_file(capture_dir, "README_CAPTURE.md", "capture instructions")
        _package_file(root, "README_RUN.md", "run instructions")
    except (OSError, json.JSONDecodeError, TypeError, AttributeError, ValueError) as exc:
        errors.append(f"capture packet validation failed: {exc}")

    return errors, manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        errors, manifest = validate_package(args.package_dir / "run-package.json")
        if errors or manifest is None:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"OK: run package {manifest['run_id']} is portable, intact and capture-ready.")
        print("No AI/provider calls or measurements were performed.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
