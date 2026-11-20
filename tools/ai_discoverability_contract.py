#!/usr/bin/env python3
"""Offline validation for the Megabrain AI Discoverability handoff contract."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "ops/ai-discoverability/AGENT_CONTRACT.json"
QUEUE = ROOT / "ops/ai-discoverability/WORK_QUEUE.json"
SCHEMA = ROOT / "schemas/ai-discoverability-work-item.schema.json"
REQUIRED = {
    "id", "title", "work_type", "priority", "status", "market", "language",
    "service", "target_surface", "obstacle", "evidence_refs", "decision_to_unlock",
    "hypothesis", "success_criteria", "autonomy_class", "requires_new_measurement",
    "measurement_guard", "expected_effort", "risk", "blocker", "unblock_condition",
    "validation_refs",
}
BLOCKED = {
    "blocked_until_region_attestation_available",
    "blocked_until_authorized_machine_access",
    "blocked_by_owner_approval",
}


def read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid or unreadable JSON: {exc}")
        return None


def validate_contract(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["agent contract must be an object"]
    if data.get("schema") != "audio-reclama/megabrain-ai-discoverability-contract/1":
        errors.append("unexpected agent contract schema")
    mission = data.get("mission", {})
    if mission.get("entity") != "Аудио-Реклама•ru":
        errors.append("mission must use the canonical brand")
    if mission.get("canonical_site") != "https://www.audio-reclama.ru":
        errors.append("mission must use the exact canonical site URL")
    if data.get("interface", {}).get("mode") != "file_based":
        errors.append("Megabrain interface must be file_based")
    policy = data.get("execution_policy", {})
    required_true = (
        "must_check_existing_evidence_before_research",
        "must_state_decision_unlocked_before_measurement",
        "must_define_measurement_stop_rule",
        "must_not_require_owner_to_collect_or_upload_data",
        "must_not_repeat_unchanged_measurements_without_a_reason",
        "must_not_treat_blocked_or_unrun_as_zero_visibility",
    )
    for key in required_true:
        if policy.get(key) is not True:
            errors.append(f"execution_policy.{key} must be true")
    autonomy = data.get("autonomy", {})
    allowed = set(autonomy.get("allowed_without_case_by_case_owner_input", []))
    approvals = set(autonomy.get("requires_explicit_owner_approval", []))
    forbidden = set(autonomy.get("forbidden", []))
    for action in ("read_repository", "build_or_update_repository_knowledge_assets", "run_local_validation_and_ci", "create_scoped_work_branch", "open_pull_request"):
        if action not in allowed:
            errors.append(f"autonomy does not allow {action}")
    for action in ("merge_into_main", "write_to_official_website", "purchase_paid_services_credits_ads_or_subscriptions"):
        if action not in approvals:
            errors.append(f"autonomy must gate {action} behind owner approval")
    for action in ("fabricate_region_or_operator_attestation", "invent_measurements_citations_customers_or_results", "write_to_or_deploy_the_official_website"):
        if action not in forbidden:
            errors.append(f"autonomy must forbid {action}")
    return errors


def validate_item(item: Any, index: int) -> list[str]:
    prefix = f"items[{index}]"
    if not isinstance(item, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    missing, extra = REQUIRED - set(item), set(item) - REQUIRED
    if missing:
        errors.append(f"{prefix} missing: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{prefix} unexpected: {', '.join(sorted(extra))}")
    if missing:
        return errors
    if not re.fullmatch(r"AI-DISC-[0-9]{4}-[0-9]{3}", str(item["id"])):
        errors.append(f"{prefix}.id has invalid format")
    if item["priority"] not in {"P0", "P1", "P2", "P3"}:
        errors.append(f"{prefix}.priority is invalid")
    if item["autonomy_class"] not in {"repository_only", "authorized_external_read_only", "requires_owner_approval"}:
        errors.append(f"{prefix}.autonomy_class is invalid")
    for field in ("title", "market", "language", "service", "target_surface", "obstacle", "decision_to_unlock", "hypothesis"):
        if not isinstance(item[field], str) or not item[field].strip():
            errors.append(f"{prefix}.{field} must be non-empty text")
    refs = item["evidence_refs"]
    if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or not x.strip() for x in refs):
        errors.append(f"{prefix}.evidence_refs must be a non-empty string array")
    elif len(refs) != len(set(refs)):
        errors.append(f"{prefix}.evidence_refs has duplicates")
    criteria = item["success_criteria"]
    if not isinstance(criteria, list) or len(criteria) < 2 or any(not isinstance(x, str) or len(x.strip()) < 8 for x in criteria):
        errors.append(f"{prefix}.success_criteria needs at least two concrete criteria")
    if not isinstance(item["requires_new_measurement"], bool):
        errors.append(f"{prefix}.requires_new_measurement must be boolean")
    guard = item["measurement_guard"]
    if item["requires_new_measurement"]:
        if not isinstance(guard, dict) or any(not isinstance(guard.get(k), str) or not guard[k].strip() for k in ("decision_to_unlock", "minimum_sufficient_sample", "stop_rule", "cost_or_access_class")):
            errors.append(f"{prefix}.measurement_guard must define decision, minimum sample, stop rule and access/cost")
    elif guard is not None:
        errors.append(f"{prefix}.measurement_guard must be null when measurement is not required")
    if item["status"] == "done" and not item["validation_refs"]:
        errors.append(f"{prefix}: done requires validation_refs")
    if item["status"] in BLOCKED:
        if not item["blocker"] or not item["unblock_condition"]:
            errors.append(f"{prefix}: blocked work requires blocker and unblock_condition")
    if item["status"] == "ready_for_agent_triage" and item["autonomy_class"] == "requires_owner_approval":
        errors.append(f"{prefix}: owner-approval work cannot be autonomous-ready")
    if item["work_type"] in {"measurement_integration", "analytics_integration"} and not item["requires_new_measurement"]:
        errors.append(f"{prefix}: measurement integration requires an explicit measurement guard")
    return errors


def validate_queue(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["work queue must be an object"]
    errors: list[str] = []
    if data.get("schema") != "audio-reclama/ai-discoverability-work-queue/1":
        errors.append("unexpected work queue schema")
    items = data.get("items")
    if not isinstance(items, list):
        return errors + ["work queue items must be an array"]
    seen: set[str] = set()
    for index, item in enumerate(items):
        errors.extend(validate_item(item, index))
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            if item["id"] in seen:
                errors.append(f"duplicate work item id: {item['id']}")
            seen.add(item["id"])
    return errors


def validate_all() -> list[str]:
    errors: list[str] = []
    contract, queue, schema = (
        read_json(CONTRACT, errors),
        read_json(QUEUE, errors),
        read_json(SCHEMA, errors),
    )
    if contract is not None:
        errors.extend(validate_contract(contract))
    if queue is not None:
        errors.extend(validate_queue(queue))
    if schema is not None:
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append("work-item schema must use JSON Schema 2020-12")
        if schema.get("additionalProperties") is not False:
            errors.append("work-item schema must reject undeclared fields")
        if not isinstance(schema.get("properties"), dict):
            errors.append("work-item schema must declare properties")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.parse_args()
    errors = validate_all()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: Megabrain AI Discoverability contract and queue are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
