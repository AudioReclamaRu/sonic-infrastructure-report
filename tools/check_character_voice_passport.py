#!/usr/bin/env python3
"""Guard the character-voice passport docs and release-gate logic.

This is a repository integrity check, not a legal compliance checker and not a
complete JSON Schema implementation. The JSON Schema is the interoperable
contract; this script exercises the critical release gates using stdlib only.
"""
from copy import deepcopy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "standards" / "CHARACTER_VOICE_PASSPORT_TEMPLATE.md"
FRAMEWORK = ROOT / "standards" / "CHARACTER_VOICE_IDENTITY_AND_CONTINUITY_FRAMEWORK.md"
EXAMPLE = ROOT / "research" / "CHARACTER_VOICE_PASSPORT_SYNTHETIC_WALKTHROUGH_2026-11-14.md"
RESEARCH_CASES = ROOT / "research" / "CHARACTER_VOICE_CONTINUITY_EXTERNAL_CASES_2026-11-14.md"
STANDARDS_INDEX = ROOT / "standards" / "README.md"
SCHEMA = ROOT / "schemas" / "character-voice-passport.schema.json"
FIXTURE = ROOT / "research" / "character-voice-passport.synthetic.json"

SCOPES = (
    "character_use", "performer_consent", "phonogram_rights", "recording_use",
    "reference_use", "distribution", "ai_training", "digital_replica",
    "localization", "data_handling",
)
USE_REQUIREMENTS = {
    "new_recording": ("character_use", "performer_consent", "recording_use"),
    "distribution": ("phonogram_rights", "distribution"),
    "reference_use": ("reference_use",),
    "ai_training": ("ai_training", "data_handling"),
    "digital_replica": ("performer_consent", "digital_replica", "data_handling"),
    "localization": ("character_use", "performer_consent", "localization", "distribution"),
}
VALID_PERMISSION_STATES = {"unknown", "pending", "approved", "denied", "not_applicable"}


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    parts = text.split("---\n", 2)
    return parts[1] if len(parts) == 3 else ""


def gate_errors(passport: dict) -> list[str]:
    errors: list[str] = []
    permissions = passport.get("permissions")
    if not isinstance(permissions, dict):
        return ["permissions must be an object"]

    missing = [scope for scope in SCOPES if scope not in permissions]
    if missing:
        return [f"missing permission scope: {scope}" for scope in missing]

    for scope in SCOPES:
        record = permissions[scope]
        if not isinstance(record, dict):
            errors.append(f"{scope} must be an object")
            continue
        state = record.get("status")
        if state not in VALID_PERMISSION_STATES:
            errors.append(f"{scope} has invalid status: {state!r}")
            continue
        if state == "approved":
            for field in ("scope", "evidence_ref", "checked_by", "checked_at"):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    errors.append(f"{scope} approved without {field}")
        if state == "not_applicable" and not str(record.get("rationale", "")).strip():
            errors.append(f"{scope} not_applicable without rationale")

    planned = passport.get("planned_uses", [])
    if not isinstance(planned, list):
        errors.append("planned_uses must be a list")
        planned = []
    for use in planned:
        if use not in USE_REQUIREMENTS:
            errors.append(f"unknown planned use: {use!r}")
            continue
        for scope in USE_REQUIREMENTS[use]:
            state = permissions.get(scope, {}).get("status")
            if state != "approved":
                errors.append(f"planned use {use} requires approved {scope}")

    if passport.get("release_decision") == "PASS":
        if passport.get("document_status") != "APPROVED":
            errors.append("PASS requires document_status APPROVED")
        approval = passport.get("release_approval")
        if not isinstance(approval, dict):
            errors.append("PASS requires release_approval")
        else:
            for field in ("approved_by", "approved_at", "decision_ref"):
                if not isinstance(approval.get(field), str) or not approval[field].strip():
                    errors.append(f"PASS approval missing {field}")
        for scope in SCOPES:
            state = permissions[scope].get("status")
            if state not in {"approved", "not_applicable"}:
                errors.append(f"PASS blocked by unresolved {scope}: {state!r}")
    return errors


def approved_test_passport(draft: dict) -> dict:
    candidate = deepcopy(draft)
    candidate["document_status"] = "APPROVED"
    candidate["release_decision"] = "PASS"
    candidate["planned_uses"] = ["new_recording", "distribution"]
    for scope in SCOPES:
        candidate["permissions"][scope] = {
            "status": "not_applicable",
            "rationale": "Not in scope for this synthetic gate test.",
        }
    for scope in (
        "character_use", "performer_consent", "recording_use",
        "phonogram_rights", "distribution",
    ):
        candidate["permissions"][scope] = {
            "status": "approved",
            "scope": f"Synthetic permission scope for {scope}",
            "evidence_ref": f"SYNTHETIC-EVIDENCE-{scope.upper()}",
            "checked_by": "SYNTHETIC-REVIEWER",
            "checked_at": "2026-11-14T00:00:00Z",
        }
    candidate["release_approval"] = {
        "approved_by": "SYNTHETIC-APPROVER",
        "approved_at": "2026-11-14T00:00:00Z",
        "decision_ref": "SYNTHETIC-RELEASE-DECISION",
    }
    return candidate


def main() -> int:
    required_files = [TEMPLATE, FRAMEWORK, EXAMPLE, RESEARCH_CASES, STANDARDS_INDEX, SCHEMA, FIXTURE]
    missing = [str(p.relative_to(ROOT)) for p in required_files if not p.is_file()]
    if missing:
        for item in missing:
            print(f"FAIL: missing required file: {item}")
        return 1

    template = TEMPLATE.read_text(encoding="utf-8")
    framework = FRAMEWORK.read_text(encoding="utf-8")
    example = EXAMPLE.read_text(encoding="utf-8")
    cases = RESEARCH_CASES.read_text(encoding="utf-8")
    index = STANDARDS_INDEX.read_text(encoding="utf-8")

    checks: dict[str, bool] = {
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

    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        draft = json.loads(FIXTURE.read_text(encoding="utf-8"))
        checks["machine-readable JSON Schema parses as draft 2020-12"] = (
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
        )
        schema_scopes = schema.get("properties", {}).get("permissions", {}).get("required", [])
        checks["schema requires all separate permission scopes"] = set(schema_scopes) == set(SCOPES)
        checks["schema contains conditional gates for release and planned uses"] = (
            len(schema.get("allOf", [])) == 1 + len(USE_REQUIREMENTS)
        )
        checks["synthetic JSON fixture is marked HOLD, never PASS"] = (
            draft.get("release_decision") == "HOLD"
            and draft.get("document_status") == "DRAFT"
        )
        checks["draft fixture accepts unresolved rights without authorizing release"] = (
            not gate_errors(draft)
        )
        passing = approved_test_passport(draft)
        checks["fully scoped synthetic PASS fixture satisfies the release gate"] = (
            not gate_errors(passing)
        )
        bad_pass = deepcopy(passing)
        bad_pass["permissions"]["ai_training"]["status"] = "unknown"
        checks["PASS is blocked if any mandatory scope is unknown"] = bool(gate_errors(bad_pass))
        bad_ai = deepcopy(draft)
        bad_ai["planned_uses"] = ["ai_training"]
        checks["AI training use requires its own explicit approval"] = bool(gate_errors(bad_ai))
        bad_reference = deepcopy(draft)
        bad_reference["planned_uses"] = ["reference_use"]
        checks["reference use requires its own explicit approval"] = bool(gate_errors(bad_reference))
        bad_replica = deepcopy(draft)
        bad_replica["planned_uses"] = ["digital_replica"]
        bad_replica["permissions"]["digital_replica"]["status"] = "denied"
        checks["digital replica cannot proceed on a denied permission"] = bool(gate_errors(bad_replica))
    except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
        print(f"FAIL: schema/fixture validation could not run: {exc}")
        return 1

    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"{'OK' if ok else 'FAIL'}: {name}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
