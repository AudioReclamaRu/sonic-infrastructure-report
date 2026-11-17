#!/usr/bin/env python3
"""Validate full AI visibility evidence records and their CSV benchmark links."""
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SCORE_KEYS = (
    "brand_identity", "official_route", "service_or_answer", "commercial_accuracy",
    "expertise_retrieval", "source_quality", "citation_quality", "git_knowledge",
)
ANSWERED = {"OK", "PARTIAL"}
NON_ANSWERED = {
    "NOT_TESTED", "NOT_AVAILABLE_IN_COUNTRY", "BLOCKED_REGION", "BLOCKED_AUTH",
    "UNSUPPORTED_PROVIDER", "BLOCKED_NETWORK", "ERROR",
}
STATUSES = ANSWERED | NON_ANSWERED
MODES = {"consumer_ui", "model_api", "search_results_ui"}
ROOT_KEYS = {
    "schema", "observation_id", "run_id", "observed_at_utc", "market",
    "platform", "query", "answer_status", "raw_answer", "answer_excerpt",
    "named_providers", "generic_discovery_hit", "critical_error", "scores",
    "evidence", "limitations", "operator_notes",
}

def _is_utc_datetime(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)

def validate_record(record: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record must be a JSON object"]
    extra = set(record) - ROOT_KEYS
    if extra:
        errors.append("unexpected top-level fields: " + ", ".join(sorted(extra)))
    required = {"schema", "observation_id", "run_id", "observed_at_utc", "market", "platform", "query", "answer_status", "raw_answer", "scores", "evidence"}
    missing = required - set(record)
    if missing:
        errors.append("missing top-level fields: " + ", ".join(sorted(missing)))
        return errors
    if record.get("schema") != "studio/ai-visibility-observation/1":
        errors.append("unexpected observation schema identifier")
    for field in ("observation_id", "run_id"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if not _is_utc_datetime(record.get("observed_at_utc")):
        errors.append("observed_at_utc must be an ISO-8601 UTC timestamp")

    market = record.get("market")
    if not isinstance(market, dict):
        errors.append("market must be an object")
    else:
        for field in ("country_code", "interface_locale", "prompt_language"):
            if not isinstance(market.get(field), str) or not market[field].strip():
                errors.append(f"market.{field} must be a non-empty string")
        country = market.get("country_code")
        if isinstance(country, str) and (len(country) != 2 or not country.isalpha() or country.upper() != country):
            errors.append("market.country_code must be a two-letter uppercase ISO code")
        for field in (
            "region", "region_evidence", "answer_language",
            "region_attestation_id", "region_attestation_sha256",
        ):
            if field in market and market[field] is not None and not isinstance(market[field], str):
                errors.append(f"market.{field} must be a string or null")

    platform = record.get("platform")
    if not isinstance(platform, dict):
        errors.append("platform must be an object")
    else:
        for field in ("id", "product", "surface"):
            if not isinstance(platform.get(field), str) or not platform[field].strip():
                errors.append(f"platform.{field} must be a non-empty string")
        if platform.get("measurement_mode") not in MODES:
            errors.append("platform.measurement_mode is invalid")

    query = record.get("query")
    if not isinstance(query, dict):
        errors.append("query must be an object")
    else:
        for field in ("query_id", "intent", "exact_prompt"):
            if not isinstance(query.get(field), str) or not query[field].strip():
                errors.append(f"query.{field} must be a non-empty string")

    status = record.get("answer_status")
    if status not in STATUSES:
        errors.append(f"answer_status must be one of {sorted(STATUSES)}")
    raw_answer = record.get("raw_answer")
    if not isinstance(raw_answer, str):
        errors.append("raw_answer must be a string")
    elif status in ANSWERED and not raw_answer.strip():
        errors.append("answered records require the complete raw_answer")
    elif status in NON_ANSWERED and raw_answer:
        errors.append("non-answer records must not contain raw_answer")

    for field in ("named_providers", "limitations"):
        value = record.get(field, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"{field} must be an array of strings")
    for field in ("generic_discovery_hit", "critical_error"):
        value = record.get(field)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field} must be boolean or null")

    scores = record.get("scores")
    if not isinstance(scores, dict):
        errors.append("scores must be an object")
    else:
        if set(scores) != set(SCORE_KEYS):
            errors.append("scores must contain exactly: " + ", ".join(SCORE_KEYS))
        for key in SCORE_KEYS:
            value = scores.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1, 2)):
                errors.append(f"scores.{key} must be 0, 1, 2 or null")
        if status in NON_ANSWERED and any(scores.get(key) is not None for key in SCORE_KEYS):
            errors.append("non-answer records cannot carry numeric scores")
    if status in NON_ANSWERED:
        if record.get("generic_discovery_hit") is not None:
            errors.append("non-answer records must set generic_discovery_hit to null")
        if record.get("critical_error") is not None:
            errors.append("non-answer records must set critical_error to null")

    evidence = record.get("evidence")
    if not isinstance(evidence, dict) or not isinstance(evidence.get("sources"), list):
        errors.append("evidence.sources must be an array")
    else:
        for index, source in enumerate(evidence["sources"], start=1):
            if not isinstance(source, dict):
                errors.append(f"evidence.sources[{index}] must be an object")
                continue
            url = source.get("url")
            parsed = urlparse(url) if isinstance(url, str) else None
            if not parsed or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append(f"evidence.sources[{index}].url must be an absolute HTTP(S) URL")
    if isinstance(evidence, dict):
        repo_files = evidence.get("repository_files", [])
        if not isinstance(repo_files, list) or any(not isinstance(item, str) for item in repo_files):
            errors.append("evidence.repository_files must be an array of strings")
    return errors

def validate_queue_links(
    records: dict[str, dict],
    queue_paths: list[Path],
    expected_region_attestation: dict | None = None,
) -> list[str]:
    """Verify each evidence record matches one exact planned queue cell."""
    errors: list[str] = []
    required = {
        "query_id", "query", "intent", "country_code", "interface_locale",
        "prompt_language", "answer_language", "platform", "platform_surface",
        "measurement_mode", "execution_status", "region_verification",
    }
    planned: dict[tuple[str, ...], dict[str, str]] = {}
    for queue_path in queue_paths:
        try:
            with queue_path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
                headers = set(reader.fieldnames or [])
        except OSError as exc:
            errors.append(f"cannot read queue CSV {queue_path}: {exc}")
            continue
        missing = sorted(required - headers)
        if missing:
            errors.append(f"queue CSV {queue_path} missing required columns: " + ", ".join(missing))
            continue
        for line, row in enumerate(rows, start=2):
            if row.get("execution_status") != "NOT_TESTED":
                errors.append(f"queue {queue_path} line {line}: planned row must remain NOT_TESTED")
            key = (
                row["query_id"], row["platform"], row["measurement_mode"],
                row["country_code"], row["interface_locale"], row["prompt_language"],
                row["answer_language"], row["platform_surface"], row["intent"], row["query"],
            )
            if key in planned:
                errors.append(f"queue {queue_path} line {line}: duplicate planned evidence identity {key[:4]}")
            planned[key] = row

    for observation_id, record in records.items():
        market = record.get("market", {})
        platform = record.get("platform", {})
        query = record.get("query", {})
        if not all(isinstance(item, dict) for item in (market, platform, query)):
            continue
        key = (
            str(query.get("query_id") or ""), str(platform.get("id") or ""),
            str(platform.get("measurement_mode") or ""),
            str(market.get("country_code") or ""), str(market.get("interface_locale") or ""),
            str(market.get("prompt_language") or ""), str(market.get("answer_language") or ""),
            str(platform.get("surface") or ""), str(query.get("intent") or ""),
            str(query.get("exact_prompt") or ""),
        )
        if key not in planned:
            errors.append(f"observation {observation_id}: no exact matching planned queue cell")
            continue
        region_status = planned[key].get("region_verification")
        if region_status == "UNVERIFIED":
            errors.append(
                f"observation {observation_id}: queue region is UNVERIFIED; "
                "evidence record does not independently establish regional verification"
            )
        elif region_status == "VERIFIED":
            if not market.get("region") or not market.get("region_evidence"):
                errors.append(
                    f"observation {observation_id}: VERIFIED region requires explicit market.region "
                    "and market.region_evidence in the primary record"
                )
            if expected_region_attestation:
                if market.get("region_attestation_id") != expected_region_attestation.get("attestation_id"):
                    errors.append(f"observation {observation_id}: region_attestation_id does not match the run passport")
                if market.get("region_attestation_sha256") != expected_region_attestation.get("sha256"):
                    errors.append(f"observation {observation_id}: region_attestation_sha256 does not match the run passport")
                capture_time = expected_region_attestation.get("session_captured_at_utc")
                observed_time = record.get("observed_at_utc")
                try:
                    capture_dt = datetime.fromisoformat(str(capture_time).replace("Z", "+00:00"))
                    observed_dt = datetime.fromisoformat(str(observed_time).replace("Z", "+00:00"))
                    if capture_dt.tzinfo is None or observed_dt.tzinfo is None or abs(observed_dt - capture_dt).total_seconds() > 1800:
                        errors.append(f"observation {observation_id}: capture time is more than 30 minutes from the verified regional session")
                except (TypeError, ValueError):
                    errors.append(f"observation {observation_id}: invalid verified regional session timestamp")
        elif region_status == "BLOCKED" and record.get("answer_status") not in {"BLOCKED_REGION", "BLOCKED_NETWORK"}:
            errors.append(
                f"observation {observation_id}: BLOCKED queue region must not be recorded as an answered observation"
            )
    return errors


def validate_observation_artifacts(
    record_paths: list[Path],
    csv_path: Path,
    queue_paths: list[Path],
    expected_run_id: str | None,
    expected_region_attestation: dict | None = None,
) -> list[str]:
    """Validate records, CSV linkage, run identity and exact queue provenance."""
    errors: list[str] = []
    if not record_paths:
        return ["no JSON observation records supplied"]
    by_id: dict[str, dict] = {}
    for path in sorted(record_paths):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: cannot read JSON: {exc}")
            continue
        for error in validate_record(record):
            errors.append(f"{path.name}: {error}")
        if isinstance(record, dict):
            if expected_run_id is not None and record.get("run_id") != expected_run_id:
                errors.append(f"{path.name}: run_id does not match the frozen run passport")
            observation_id = record.get("observation_id")
            if isinstance(observation_id, str) and observation_id:
                if observation_id in by_id:
                    errors.append(f"duplicate observation_id across records: {observation_id}")
                by_id[observation_id] = record
    if queue_paths:
        errors.extend(validate_queue_links(by_id, queue_paths, expected_region_attestation))
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
    except OSError as exc:
        return errors + [f"cannot read benchmark CSV: {exc}"]
    seen_ids: set[str] = set()
    for line, row in enumerate(rows, start=2):
        observation_id = (row.get("observation_id") or "").strip()
        status = (row.get("answer_status") or "").strip().upper()
        if status in ANSWERED and not observation_id:
            errors.append(f"CSV line {line}: answered row is missing observation_id")
            continue
        if not observation_id:
            continue
        if observation_id in seen_ids:
            errors.append(f"CSV line {line}: duplicate observation_id {observation_id}")
            continue
        seen_ids.add(observation_id)
        record = by_id.get(observation_id)
        if record is None:
            errors.append(f"CSV line {line}: no JSON record for observation_id {observation_id}")
            continue
        market = record.get("market", {})
        platform = record.get("platform", {})
        query = record.get("query", {})
        expected = {
            "run_id": expected_run_id or record.get("run_id"), "country_code": market.get("country_code"),
            "interface_locale": market.get("interface_locale"),
            "prompt_language": market.get("prompt_language"),
            "answer_language": market.get("answer_language") or "",
            "platform": platform.get("id"), "platform_surface": platform.get("surface"),
            "measurement_mode": platform.get("measurement_mode"),
            "query_id": query.get("query_id"), "intent": query.get("intent"),
            "query": query.get("exact_prompt"), "answer_status": record.get("answer_status"),
        }
        for field, value in expected.items():
            if (row.get(field) or "").strip() != str(value or ""):
                errors.append(f"CSV line {line}: {field} does not match evidence record {observation_id}")
    unlinked = set(by_id) - seen_ids
    if unlinked:
        errors.append("JSON records not linked from CSV: " + ", ".join(sorted(unlinked)))
    return errors


def validate_batch(
    records_dir: Path,
    csv_path: Path | None = None,
    queue_path: Path | None = None,
    *,
    queue_paths: list[Path] | None = None,
    expected_run_id: str | None = None,
    expected_region_attestation: dict | None = None,
) -> list[str]:
    paths = sorted(records_dir.glob("*.json")) if records_dir.is_dir() else []
    if not paths:
        return [f"no JSON observation records found in {records_dir}"]
    queues = queue_paths or ([queue_path] if queue_path else [])
    if csv_path is not None:
        return validate_observation_artifacts(
            paths, csv_path, queues, expected_run_id, expected_region_attestation
        )
    errors: list[str] = []
    by_id: dict[str, dict] = {}
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: cannot read JSON: {exc}")
            continue
        for error in validate_record(record):
            errors.append(f"{path.name}: {error}")
        if isinstance(record, dict):
            if expected_run_id is not None and record.get("run_id") != expected_run_id:
                errors.append(f"{path.name}: run_id does not match expected run")
            observation_id = record.get("observation_id")
            if isinstance(observation_id, str) and observation_id:
                if observation_id in by_id:
                    errors.append(f"duplicate observation_id across records: {observation_id}")
                by_id[observation_id] = record
    if queues:
        errors.extend(validate_queue_links(by_id, queues, expected_region_attestation))
    return errors

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("validate-record", help="validate one full JSON observation record")
    one.add_argument("record", type=Path)
    batch = sub.add_parser("validate-batch", help="validate a directory of records and optional CSV links")
    batch.add_argument("records_dir", type=Path)
    batch.add_argument("--csv", type=Path)
    batch.add_argument("--queue", type=Path, action="append", default=[], help="also require exact match to a planned execution queue; repeat for multiple queues")
    batch.add_argument("--run-id", help="require every record and CSV row to belong to this exact run ID")
    args = parser.parse_args(argv)
    if args.command == "validate-record":
        try:
            record = json.loads(args.record.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors = [f"cannot read JSON record: {exc}"]
        else:
            errors = validate_record(record)
    else:
        errors = validate_batch(args.records_dir, args.csv, queue_paths=args.queue, expected_run_id=args.run_id)
    if errors:
        print("AI visibility evidence validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    print("AI visibility evidence OK.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
