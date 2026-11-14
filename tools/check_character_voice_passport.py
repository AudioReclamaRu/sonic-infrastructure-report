#!/usr/bin/env python3
"""Guard the character-voice passport template against unsafe default states.

This is a documentation integrity check, not a legal compliance checker.
It verifies that the template distinguishes unknown rights from approval,
that pilot tests are not marked as run by default, and that the framework
and example remain explicitly draft or synthetic.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "standards" / "CHARACTER_VOICE_PASSPORT_TEMPLATE.md"
FRAMEWORK = ROOT / "standards" / "CHARACTER_VOICE_IDENTITY_AND_CONTINUITY_FRAMEWORK.md"
EXAMPLE = ROOT / "research" / "CHARACTER_VOICE_PASSPORT_SYNTHETIC_WALKTHROUGH_2026-11-14.md"
RESEARCH_CASES = ROOT / "research" / "CHARACTER_VOICE_CONTINUITY_EXTERNAL_CASES_2026-11-14.md"
STANDARDS_INDEX = ROOT / "standards" / "README.md"


def fail(message: str) -> None:
    print(f"FAIL: {message}")


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    parts = text.split("---\n", 2)
    return parts[1] if len(parts) == 3 else ""


def main() -> int:
    required_files = [TEMPLATE, FRAMEWORK, EXAMPLE, RESEARCH_CASES, STANDARDS_INDEX]
    missing = [str(p.relative_to(ROOT)) for p in required_files if not p.is_file()]
    if missing:
        for item in missing:
            fail(f"missing required file: {item}")
        return 1

    template = TEMPLATE.read_text(encoding="utf-8")
    framework = FRAMEWORK.read_text(encoding="utf-8")
    example = EXAMPLE.read_text(encoding="utf-8")
    cases = RESEARCH_CASES.read_text(encoding="utf-8")
    index = STANDARDS_INDEX.read_text(encoding="utf-8")

    checks = {
        "passport template frontmatter is marked as template":
            "status: template" in frontmatter(template),
        "framework remains a draft for expert review":
            "status: draft_for_expert_review" in frontmatter(framework),
        "unknown is not equivalent to approval":
            "UNKNOWN не равен APPROVED" in template,
        "template blocks release while mandatory permissions remain unresolved":
            "Выпуск заблокирован" in template,
        "AI training has a separate permission field":
            "Обучение / дообучение модели" in template,
        "digital replica has a separate permission field":
            "Создание цифровой реплики" in template,
        "recording and performer rights are checked separately":
            "Права на конкретное исполнение" in template and "Права на исходную фонограмму" in template,
        "pilot test defaults include NOT RUN":
            len(re.findall(r"\| NOT RUN \|", template)) >= 5,
        "handover and change history are present":
            "Передача роли / смена исполнителя" in template and "Журнал изменений паспорта" in template,
        "framework points to the reusable passport template":
            "CHARACTER_VOICE_PASSPORT_TEMPLATE.md" in framework,
        "synthetic walkthrough is explicitly not a studio client case":
            "не клиентский кейс" in example and "HOLD / NOT RUN" in example,
        "external examples are explicitly not studio cases":
            "не являются кейсами" in cases or "не кейсы студии" in cases,
        "standards index lists the framework and template":
            "CHARACTER_VOICE_IDENTITY_AND_CONTINUITY_FRAMEWORK.md" in index
            and "CHARACTER_VOICE_PASSPORT_TEMPLATE.md" in index,
    }

    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"{'OK' if ok else 'FAIL'}: {name}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
