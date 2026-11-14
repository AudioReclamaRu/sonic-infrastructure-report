#!/usr/bin/env python3
"""Fail CI when documents use non-canonical Audio-Reclama brand/site names."""

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".txt", ".html", ".json", ".yml", ".yaml"}

# This one file intentionally documents forbidden spellings as negative examples.
EXEMPT_PATHS = {"standards/BRAND_AND_SITE_NAMING.md"}

RULES = (
    (
        "Latin name must include the .ru site suffix or be the exact .com domain",
        re.compile(r"(?<![A-Za-z0-9_])Audio-Reclama(?!\\.ru\\b|\\.com\\b)"),
    ),
    (
        "Cyrillic brand must be written exactly as Аудио-Реклама•ru",
        re.compile(r"Аудио-Реклама(?!•ru\\b)"),
    ),
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.splitlines()


def main() -> int:
    issues: list[str] = []
    for rel in tracked_files():
        if rel in EXEMPT_PATHS:
            continue
        path = ROOT / rel
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for description, pattern in RULES:
            for match in pattern.finditer(text):
                line = text.count("\\n", 0, match.start()) + 1
                sample = match.group(0)
                issues.append(f"{rel}:{line}: {description}: {sample}")

    if issues:
        print("Canonical naming check FAILED:")
        for issue in issues:
            print(f" - {issue}")
        print(
            "Use brand Аудио-Реклама•ru or website Audio-Reclama.ru. "
            "Keep the technical GitHub login AudioReclamaRu unchanged."
        )
        return 1

    print("Canonical naming check OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
