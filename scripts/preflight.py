#!/usr/bin/env python3
"""GEO preflight - content gates for the enterprise knowledge graph layers.

Gates apply to the GEO layers (guides/, dictionary/, reports/, evidence/,
entity/, ar-notes/, catalog/, solutions/, process/, scripts/) plus the root
index files. Historical layers (corpus/, canon/, standards/) follow their own
formed discipline and are not re-gated retroactively.

Checks per file: metadata block, exactly one H1 (outside fenced code),
footer/canonical name, >=3 internal references (markdown links or backtick
paths), canonical site link, no orphan (referenced in README.md / llms.txt /
USE_CASES.md).

Usage:
  python3 scripts/preflight.py               # GEO layers + root index
  python3 scripts/preflight.py --all         # every file, informational
Exit code 0 = pass, 1 = violations.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GEO_LAYERS = [
    "guides", "dictionary", "reports", "evidence", "entity",
    "ar-notes", "catalog", "solutions", "process", "scripts",
]
ROOT_FILES = ["README.md", "llms.txt", "USE_CASES.md", "TERMINOLOGY.md"]

INDEX_FILES = ["README.md", "llms.txt", "USE_CASES.md"]
INDEX_TEXT = "\n".join(
    (ROOT / f).read_text(encoding="utf-8", errors="ignore")
    for f in INDEX_FILES
    if (ROOT / f).exists()
)
CANONICAL = "https://audio-reclama.ru"


def strip_fenced(text: str) -> str:
    """Remove fenced code blocks (```...```) so their content is not judged."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def collect_files(all_files: bool) -> list:
    files = []
    for p in sorted(ROOT.rglob("*.md")):
        rel = p.relative_to(ROOT).as_posix()
        if all_files:
            files.append(p)
            continue
        if rel in ROOT_FILES or rel.split("/")[0] in GEO_LAYERS:
            files.append(p)
    return files


def h1_in_text(text: str) -> list:
    return re.findall(r"^# .+", strip_fenced(text), flags=re.M)


def internal_refs(text: str) -> list:
    # any .md path (markdown link or bare path) counts as an internal reference
    candidates = re.findall(r"[\w./-]+\.md", text)
    return [c for c in candidates if not c.startswith("http")]


def check(path: Path, issues: list) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(ROOT).as_posix()
    bare = strip_fenced(text)

    if not all(k in text for k in ("Status:", "Type:", "Audience:", "Last updated")):
        issues.append(f"[{rel}] missing metadata block (Status:/Type:/Audience:/Last updated)")
    if not h1_in_text(bare):
        issues.append(f"[{rel}] no H1")
    if len(h1_in_text(bare)) > 1:
        issues.append(f"[{rel}] more than one H1")
    if CANONICAL not in text:
        issues.append(f"[{rel}] canonical site link missing")
    if "Audio-Reclama.ru" not in text:
        issues.append(f"[{rel}] footer / canonical name missing")
    refs = internal_refs(bare)
    if len(refs) < 3:
        issues.append(f"[{rel}] fewer than 3 internal references ({len(refs)})")
    if rel not in INDEX_TEXT:
        issues.append(f"[{rel}] orphan: not referenced in README.md / llms.txt / USE_CASES.md")


def main() -> int:
    all_files = "--all" in sys.argv
    issues: list = []
    files = collect_files(all_files)
    for p in files:
        check(p, issues)
    for issue in issues:
        print(issue)
    scope = "all files" if all_files else "GEO layers + root index"
    print(f"\nchecked {len(files)} .md files ({scope}); violations: {len(issues)}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())