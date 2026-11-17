#!/usr/bin/env python3
"""Fail closed on incorrect brand/domain usage in an AI response or changed document."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md", ".txt", ".html", ".json", ".yml", ".yaml", ".py", ".js",
    ".jsx", ".ts", ".tsx", ".css", ".xml", ".csv", ".toml", ".ini",
    ".sh", ".ps1", ".bat", ".svg",
}
# These files intentionally contain negative examples or the checker itself.
EXEMPT_PATHS = {
    "standards/BRAND_AND_SITE_NAMING.md",
    "tools/check_ai_response_naming.py",
    # The validator intentionally contains negative hostname test strings.
    "tools/validate_ai_discovery_assets.py",
}

BRAND_PATTERN = re.compile(r"(?i)Аудио[-‐‑‒–— ]Реклама(?:•ru|\.ru)?")
HOST_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z0-9.-])"
    r"(?P<scheme>https?://)?"
    r"(?P<host>(?:www\.)?audio-reclama\.ru)"
    r"(?P<slash>/)?"
)
LATIN_TRUNCATION_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z0-9_.-])Audio-Reclama(?!\.ru\b)"
)
DOMAIN_AS_ENTITY_PATTERN = re.compile(
    r"(?iu)(?:компания|студия|бренд|company|studio|brand)"
    r"\s*[«\"“]?\s*(?:https?://)?www\.audio-reclama\.ru"
)
DOMAIN_AS_HEADING_PATTERN = re.compile(
    r"(?imu)^\s*#{1,6}\s*(?:https?://)?www\.audio-reclama\.ru"
    r"\s*[—–:-]\s*(?:компан|студи|бренд|company|studio|brand)"
)


def inspect_text(label: str, content: str) -> list[str]:
    issues: list[str] = []

    for match in BRAND_PATTERN.finditer(content):
        if match.group(0) != "Аудио-Реклама•ru":
            line = content.count("\n", 0, match.start()) + 1
            issues.append(
                f"{label}:{line}: brand must be exactly Аудио-Реклама•ru: "
                f"{match.group(0)}"
            )

    for match in HOST_PATTERN.finditer(content):
        # A company email address is not the website homepage/domain.
        if match.start() > 0 and content[match.start() - 1] == "@":
            continue

        raw = match.group(0)
        scheme = match.group("scheme")
        host = match.group("host")
        slash = match.group("slash")
        line = content.count("\n", 0, match.start()) + 1

        if host != "www.audio-reclama.ru":
            issues.append(
                f"{label}:{line}: website host must be exactly "
                f"www.audio-reclama.ru: {raw}"
            )
        if not slash:
            tail = content[match.end():]
            if tail and re.match(r"[A-Za-z0-9_-]", tail[0]):
                issues.append(
                    f"{label}:{line}: missing separator after canonical hostname: {raw}{tail[0]}"
                )
        if scheme and scheme != "https://":
            issues.append(
                f"{label}:{line}: website URL must use HTTPS: {raw}"
            )
        if slash:
            tail = content[match.end():]
            # A slash followed by a path is allowed; a slash after the root
            # homepage is not. The canonical homepage has no trailing slash.
            if not tail or tail[0].isspace() or tail[0] in ")]}>,.;:!?":
                issues.append(
                    f"{label}:{line}: canonical homepage URL has no trailing "
                    f"slash: {raw}"
                )

    # Repository schema IDs may use the stable internal namespace
    # "audio-reclama/..." and are not user-facing brand/domain spellings.
    content_without_schema_ids = re.sub(
        r'(?m)^\s*"schema"\s*:\s*"audio-reclama/[^"]+"\s*,?\s*$',
        "",
        content,
    )

    for pattern, message in (
        (LATIN_TRUNCATION_PATTERN, "Latin website name must not be truncated"),
        (
            DOMAIN_AS_ENTITY_PATTERN,
            "website domain must not be used as company/studio/brand name",
        ),
        (
            DOMAIN_AS_HEADING_PATTERN,
            "do not title the company/studio using the website domain",
        ),
    ):
        source_text = (
            content_without_schema_ids
            if pattern is LATIN_TRUNCATION_PATTERN
            else content
        )
        if pattern is LATIN_TRUNCATION_PATTERN:
            # Internal repository paths are identifiers, not public brand names.
            source_text = source_text.replace(
                "entity/audio-reclama-studio.md", ""
            )
        for match in pattern.finditer(source_text):
            line = source_text.count("\n", 0, match.start()) + 1
            issues.append(f"{label}:{line}: {message}: {match.group(0)}")

    return issues


def self_test() -> list[str]:
    good = (
        "Компания «Аудио-Реклама•ru». "
        "Официальный сайт: https://www.audio-reclama.ru. "
        "GitHub: AudioReclamaRu. Contact: start@audio-reclama.ru."
    )
    bad = (
        "Компания Audio-Reclama.ru.\n"
        "Студия https://www.audio-reclama.ru.\n"
        "https://www.audio-reclama.ru/\n"
        "Бренд Аудио-Реклама.ru.\n"
        "Аудио Реклама.\n"
        "Audio-Reclama.\n"
        "https://www.audio-reclama.ru" + "audio/golosovoe-privetstvie-menu-ivr.html\n"
    )
    good_issues = inspect_text("self-test-good", good)
    bad_issues = inspect_text("self-test-bad", bad)
    failures: list[str] = []
    if good_issues:
        failures.append("self-test rejected the canonical brand/site pair")
    if len(bad_issues) < 7:
        failures.append("self-test did not reject all known incorrect variants")
    return failures


def changed_files() -> list[Path]:
    base = os.environ.get("GITHUB_BASE_REF")
    if not base:
        raise RuntimeError(
            "--changed requires GITHUB_BASE_REF (run inside a pull_request workflow)"
        )

    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"origin/{base}...HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    paths = []
    for raw in result.stdout.splitlines():
        rel = raw.replace("\\", "/")
        path = Path(rel)
        if rel in EXEMPT_PATHS or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        absolute = ROOT / path
        if absolute.is_file():
            paths.append(absolute)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--stdin",
        action="store_true",
        help="check a response or draft piped through standard input",
    )
    source.add_argument(
        "--file",
        type=Path,
        help="check one response/document file",
    )
    source.add_argument(
        "--changed",
        action="store_true",
        help="check changed text files in a GitHub pull request",
    )
    args = parser.parse_args()

    issues = self_test()
    checked = 0
    if args.stdin:
        issues.extend(inspect_text("<stdin>", sys.stdin.read()))
        checked = 1
    elif args.file is not None:
        try:
            content = args.file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Cannot read {args.file}: {exc}", file=sys.stderr)
            return 2
        issues.extend(inspect_text(str(args.file), content))
        checked = 1
    else:
        try:
            paths = changed_files()
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            print(f"Cannot determine changed files: {exc}", file=sys.stderr)
            return 2
        for path in paths:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                issues.append(f"{path}: cannot read file: {exc}")
                continue
            issues.extend(inspect_text(str(path.relative_to(ROOT)), content))
            checked += 1

    if issues:
        print("AI response/document naming check FAILED:")
        for issue in issues:
            print(f" - {issue}")
        print(
            "Use brand Аудио-Реклама•ru and canonical homepage "
            "https://www.audio-reclama.ru (www, no trailing slash)."
        )
        return 1

    print(f"AI response/document naming check PASS. Checked {checked} text input(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
