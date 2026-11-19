#!/usr/bin/env python3
"""Validate evidence card IDs against the repository-wide allocation registry.

The registry prevents duplicate IDs across parallel pull requests. New evidence
files must be registered to the exact branch that adds them.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ID_RE = re.compile(r"^E-2026-\d{3}$")
FILE_RE = re.compile(r"^E-2026-\d{3}\.md$")
FRONTMATTER_ID_RE = re.compile(r"(?m)^id:\s*(E-2026-\d{3})\s*$")
REGISTRY_FIELDS = ("evidence_id", "path", "allocated_branch", "notes")


def frontmatter_id(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    match = FRONTMATTER_ID_RE.search(text[4:end])
    return match.group(1) if match else None


def added_evidence_paths(root: Path, base_ref: str) -> list[str]:
    """Return evidence card paths newly added relative to the PR base."""
    result = subprocess.run(
        ["git", "diff", "--name-status", "--diff-filter=A", f"{base_ref}...HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[0] == "A":
            path = parts[1].replace("\\", "/")
            if path.startswith("evidence/E-2026-") and path.endswith(".md"):
                paths.append(path)
    return paths


def validate_registry(
    root: Path,
    *,
    branch_name: str | None = None,
    added_paths: Iterable[str] = (),
) -> list[str]:
    errors: list[str] = []
    evidence_dir = root / "evidence"
    registry_path = evidence_dir / "ID_REGISTRY.csv"
    if not registry_path.is_file():
        return [f"registry is missing: {registry_path.relative_to(root)}"]

    by_id: dict[str, dict[str, str]] = {}
    by_path: dict[str, str] = {}
    try:
        with registry_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != REGISTRY_FIELDS:
                return [
                    "registry columns must be exactly: "
                    + ", ".join(REGISTRY_FIELDS)
                ]
            for line_no, row in enumerate(reader, start=2):
                evidence_id = (row.get("evidence_id") or "").strip()
                path = (row.get("path") or "").strip().replace("\\", "/")
                owner = (row.get("allocated_branch") or "").strip()
                if not ID_RE.fullmatch(evidence_id):
                    errors.append(f"registry line {line_no}: invalid evidence_id {evidence_id!r}")
                    continue
                expected_path = f"evidence/{evidence_id}.md"
                if path != expected_path:
                    errors.append(
                        f"registry line {line_no}: {evidence_id} path must be {expected_path}"
                    )
                if not owner:
                    errors.append(f"registry line {line_no}: allocated_branch is required")
                if evidence_id in by_id:
                    errors.append(f"duplicate registry ID: {evidence_id}")
                    continue
                if path in by_path:
                    errors.append(f"duplicate registry path: {path}")
                    continue
                by_id[evidence_id] = row
                by_path[path] = evidence_id
    except OSError as exc:
        return [f"cannot read evidence ID registry: {exc}"]

    actual_files = sorted(evidence_dir.glob("E-2026-*.md"))
    seen_frontmatter: dict[str, str] = {}
    for path in actual_files:
        relative = path.relative_to(root).as_posix()
        if not FILE_RE.fullmatch(path.name):
            errors.append(f"invalid evidence filename: {relative}")
            continue
        filename_id = path.stem
        recorded_id = frontmatter_id(path)
        if recorded_id is None:
            errors.append(f"{relative}: missing valid id in YAML frontmatter")
        elif recorded_id != filename_id:
            errors.append(
                f"{relative}: frontmatter ID {recorded_id} does not match filename {filename_id}"
            )
        if filename_id in seen_frontmatter:
            errors.append(
                f"duplicate evidence filename ID {filename_id}: "
                f"{seen_frontmatter[filename_id]} and {relative}"
            )
        else:
            seen_frontmatter[filename_id] = relative

        row = by_id.get(filename_id)
        if row is None:
            errors.append(f"{relative}: ID is not allocated in ID_REGISTRY.csv")
            continue
        if row.get("path", "").strip().replace("\\", "/") != relative:
            errors.append(f"{relative}: registry points this ID to another path")

    for evidence_id, row in by_id.items():
        path = row.get("path", "").strip().replace("\\", "/")
        target = root / path
        owner = row.get("allocated_branch", "").strip()
        if owner == "main" and not target.is_file():
            errors.append(f"{evidence_id}: main allocation has no evidence file at {path}")
        if target.is_file():
            recorded_id = frontmatter_id(target)
            if recorded_id != evidence_id:
                errors.append(
                    f"{path}: registry ID {evidence_id} does not match frontmatter {recorded_id!r}"
                )

    added = list(added_paths)
    if branch_name:
        for raw_path in added:
            path = raw_path.replace("\\", "/")
            if not path.startswith("evidence/E-2026-") or not path.endswith(".md"):
                continue
            match = re.fullmatch(r"evidence/(E-2026-\d{3})\.md", path)
            if not match:
                errors.append(f"new evidence path has invalid name: {path}")
                continue
            evidence_id = match.group(1)
            row = by_id.get(evidence_id)
            if row is None:
                errors.append(f"{path}: newly added ID is not reserved in ID_REGISTRY.csv")
            elif row.get("allocated_branch", "").strip() != branch_name:
                errors.append(
                    f"{path}: ID is allocated to branch "
                    f"{row.get('allocated_branch')!r}, not current branch {branch_name!r}"
                )
    elif added:
        errors.append("branch_name is required when validating newly added evidence files")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to this script's repository)",
    )
    parser.add_argument("--branch-name", help="current pull request head branch")
    parser.add_argument("--base-ref", help="git ref for the pull request base")
    args = parser.parse_args()

    if bool(args.branch_name) != bool(args.base_ref):
        parser.error("--branch-name and --base-ref must be supplied together")

    changed: list[str] = []
    if args.base_ref:
        try:
            changed = added_evidence_paths(args.root.resolve(), args.base_ref)
        except subprocess.CalledProcessError as exc:
            print(
                f"FAIL: unable to compare PR base {args.base_ref}: "
                f"{exc.stderr.strip()}",
                file=sys.stderr,
            )
            return 2

    errors = validate_registry(
        args.root.resolve(),
        branch_name=args.branch_name,
        added_paths=changed,
    )
    if errors:
        print("FAIL: evidence ID registry")
        for error in errors:
            print(f"- {error}")
        return 1

    files = len(list((args.root / "evidence").glob("E-2026-*.md")))
    print(
        f"PASS: evidence ID registry; {files} evidence files and "
        f"{len(changed)} newly allocated evidence files checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
