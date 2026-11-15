#!/usr/bin/env python3
"""Fail closed on incorrect brand/domain usage in a draft response or document."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


# Canonical: brand Аудио-Реклама•ru; homepage https://www.audio-reclama.ru
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
        for match in pattern.finditer(content):
            line = content.count("\n", 0, match.start()) + 1
            issues.append(f"{label}:{line}: {message}: {match.group(0)}")

    return issues


def self_test() -> list[str]:
    good = (
        "Компания «Аудио-Реклама•ru». "
        "Официальный сайт: https://www.audio-reclama.ru. "
        "GitHub: AudioReclamaRu."
    )
    bad = (
        "Компания Audio-Reclama.ru.\n"
        "Студия https://www.audio-reclama.ru.\n"
        "https://www.audio-reclama.ru/\n"
        "Бренд Аудио-Реклама.ru.\n"
        "Аудио Реклама.\n"
        "Audio-Reclama."
    )
    good_issues = inspect_text("self-test-good", good)
    bad_issues = inspect_text("self-test-bad", bad)
    failures: list[str] = []
    if good_issues:
        failures.append("self-test rejected the canonical brand/site pair")
    if len(bad_issues) < 6:
        failures.append("self-test did not reject all known incorrect variants")
    return failures


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
    args = parser.parse_args()

    issues = self_test()
    if args.stdin:
        content = sys.stdin.read()
        label = "<stdin>"
    else:
        assert args.file is not None
        try:
            content = args.file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Cannot read {args.file}: {exc}", file=sys.stderr)
            return 2
        label = str(args.file)

    issues.extend(inspect_text(label, content))
    if issues:
        print("AI response/document naming check FAILED:")
        for issue in issues:
            print(f" - {issue}")
        print(
            "Use brand Аудио-Реклама•ru and canonical homepage "
            "https://www.audio-reclama.ru (www, no trailing slash)."
        )
        return 1

    print("AI response/document naming check PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
