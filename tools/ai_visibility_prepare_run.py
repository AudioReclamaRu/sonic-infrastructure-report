#!/usr/bin/env python3
"""Bootstrap a verified AI-visibility run package without performing measurements."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.ai_visibility_capture import build_packet
from tools.ai_visibility_queue import build_rows, load_module, write_queue
from tools.ai_visibility_region import validate_attestation
from tools.ai_visibility_run import create_plan, validate_plan, write_json

PACKAGE_SCHEMA = "studio/ai-visibility-run-package/1"


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_files(value: Any) -> set[str]:
    """Collect attestation evidence_file references without rewriting the attestation."""
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_file" and isinstance(item, str) and item.strip():
                found.add(item)
            else:
                found.update(_evidence_files(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_evidence_files(item))
    return found


def _copy_region_inputs(attestation: dict[str, Any], source_dir: Path, target_dir: Path) -> None:
    """Copy exact evidence bytes while preserving attestation-relative paths."""
    source_root = source_dir.resolve(strict=True)
    snapshots: list[tuple[Path, Path]] = []
    for relative_name in sorted(_evidence_files(attestation)):
        # Attestation paths are portable POSIX-relative paths, regardless of the
        # operating system performing package preparation.
        relative = Path(relative_name)
        if (
            relative.is_absolute()
            or "\\" in relative_name
            or re.match(r"^[A-Za-z]:", relative_name)
            or ".." in relative.parts
            or "." in relative.parts
            or not relative.parts
        ):
            raise ValueError(f"regional evidence path must be a portable relative path inside the attestation directory: {relative_name}")
        source = (source_root / relative).resolve(strict=True)
        try:
            source.relative_to(source_root)
        except ValueError as exc:
            raise ValueError(f"regional evidence path escapes attestation directory: {relative_name}") from exc
        if not source.is_file():
            raise ValueError(f"regional evidence artifact is not a regular file: {relative_name}")
        snapshots.append((source, relative))

    target_dir.mkdir(parents=True, exist_ok=True)
    for source, relative in snapshots:
        destination = target_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def prepare_run(
    module_path: Path,
    attestation_path: Path,
    run_id: str,
    output_dir: Path,
    operator_label: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    module_path = module_path.resolve(strict=True)
    attestation_path = attestation_path.resolve(strict=True)
    if output_dir.exists():
        raise ValueError(f"output directory already exists; refusing to overwrite: {output_dir}")
    if not run_id.strip():
        raise ValueError("run_id must be a non-empty label")

    module = load_module(module_path)
    attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    attestation_errors, attestation_status = validate_attestation(
        attestation, attestation_path.parent
    )
    if attestation_errors or attestation_status != "VERIFIED":
        raise ValueError("regional attestation is not VERIFIED: " + "; ".join(attestation_errors or [attestation_status]))

    rows = build_rows(module, region_status="VERIFIED")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ai-visibility-run-", dir=output_dir.parent) as temporary:
        stage = Path(temporary) / "package"
        stage.mkdir()
        inputs_dir = stage / "inputs"
        module_snapshot = inputs_dir / "query-module" / module_path.name
        module_snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(module_path, module_snapshot)
        attestation_snapshot_dir = inputs_dir / "region-attestation"
        attestation_snapshot = attestation_snapshot_dir / "attestation.json"
        attestation_snapshot_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(attestation_path, attestation_snapshot)
        _copy_region_inputs(attestation, attestation_path.parent, attestation_snapshot_dir)

        queue_path = stage / "queue.csv"
        passport_path = stage / "passport.json"
        write_queue(rows, queue_path)
        args = Namespace(
            output=passport_path,
            run_id=run_id,
            module=[str(module_snapshot)],
            queue=[str(queue_path)],
            region_status="VERIFIED",
            region_attestation=attestation_snapshot,
            operator_label=operator_label,
            notes=notes,
        )
        write_json(passport_path, create_plan(args))
        errors, passport = validate_plan(passport_path)
        if errors or passport is None:
            raise ValueError("generated run passport failed validation: " + "; ".join(errors))
        packet = build_packet(passport_path, stage / "capture-packet")
        manifest = {
            "schema": PACKAGE_SCHEMA,
            "package_status": "PLANNED_CAPTURE_READY",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "run_id": run_id,
            "query_module": {
                "path": "inputs/query-module/" + module_snapshot.name,
                "filename": module_snapshot.name,
                "sha256": digest_file(module_snapshot),
            },
            "queue": {
                "path": "queue.csv",
                "sha256": digest_file(queue_path),
                "planned_cells": len(rows),
            },
            "region_attestation": {
                "path": "inputs/region-attestation/attestation.json",
                "attestation_id": attestation.get("attestation_id"),
                "sha256": digest_file(attestation_snapshot),
            },
            "plan_passport": {
                "path": "passport.json",
                "sha256": passport["passport_sha256"],
            },
            "capture_packet": {
                "path": "capture-packet/",
                "manifest_schema": packet["schema"],
                "planned_cells": packet["planned_cells"],
            },
            "semantics": [
                "This package contains a frozen plan and blank capture templates, not observations.",
                "No provider or AI service has been queried.",
                "The regional attestation must remain valid for the actual collection session; every observation is limited to its 30-minute session window.",
            ],
        }
        write_json(stage / "run-package.json", manifest)
        readme = f"""# Prepared AI Visibility Run

- Run ID: {run_id}
- Planned cells: {len(rows)}
- Region status: VERIFIED
- Region attestation: {attestation.get('attestation_id')}
- Query module SHA-256: {digest_file(module_path)}
- Plan passport SHA-256: {passport['passport_sha256']}

## Contents

- inputs/query-module/ — exact frozen query-module bytes
- inputs/region-attestation/ — exact attestation and referenced evidence bytes
- queue.csv — frozen execution queue
- passport.json — immutable plan passport
- capture-packet/ — blank CSV and JSON templates for manual capture
- run-package.json — package manifest

## Next action

First run the offline package integrity check: `python tools/ai_visibility_package.py --package-dir <this-package-directory>`. Then review capture-packet/README_CAPTURE.md. The package contains no observations. Fill the templates only from actual consumer sessions, then run the evidence validator, finalize the result passport, validate it and generate the final report.

Do not use a VPN, proxy, cloud host or remote desktop for the RU consumer baseline. Every observation must be within 30 minutes of the verified session capture. If the session window expires, create a new attestation and a new run package.
"""
        (stage / "README_RUN.md").write_text(readme, encoding="utf-8")
        stage.rename(output_dir)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, type=Path)
    parser.add_argument("--region-attestation", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--operator-label")
    parser.add_argument("--notes")
    args = parser.parse_args(argv)
    try:
        manifest = prepare_run(
            args.module, args.region_attestation, args.run_id,
            args.output_dir, args.operator_label, args.notes,
        )
        print(f"PASS: prepared run {manifest['run_id']} with {manifest['queue']['planned_cells']} planned cells")
        print("No measurements or observations were created.")
        return 0
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
