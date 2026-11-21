#!/usr/bin/env python3
"""Reject malformed concatenation of the canonical site host and a URL path."""

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".csv", ".txt", ".html", ".json", ".yml", ".yaml"}
MALFORMED_CANONICAL_URL = re.compile(
    r"https?://(?:www\.)?audio[-]reclama[.]ru[A-Za-z0-9_-][^\s<>\"']*",
    re.IGNORECASE,
)


def find_malformed_domain_joins(text: str) -> list[tuple[int, str]]:
    """Return (1-based line, malformed URL) for paths joined directly to .ru."""
    problems: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in MALFORMED_CANONICAL_URL.finditer(line):
            problems.append((line_number, match.group(0)))
    return problems


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [
        item.decode("utf-8", errors="replace")
        for item in result.stdout.split(b"\0")
        if item
    ]


def main() -> int:
    checked_files = 0
    issues: list[str] = []
    try:
        paths = tracked_files()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Cannot enumerate tracked files: {exc}")
        return 2

    for relative_path in paths:
        path = ROOT / relative_path
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        checked_files += 1
        for line_number, malformed_url in find_malformed_domain_joins(content):
            issues.append(
                f"{relative_path}:{line_number}: malformed URL: {malformed_url}"
            )

    if issues:
        print("Internal URL boundary check FAILED:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    print(f"Internal URL boundary check OK ({checked_files} tracked text files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
