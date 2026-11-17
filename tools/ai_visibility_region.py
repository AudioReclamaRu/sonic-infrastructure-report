#!/usr/bin/env python3
"""Offline validator for evidence-backed regional vantage-point attestations."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "studio/ai-visibility-region-attestation/1"
ROOT_FIELDS = {
    "schema", "attestation_id", "observed_at_utc", "country_code",
    "interface_locale", "network", "geolocation_sources",
    "network_owner_evidence", "session_capture", "operator_declaration", "review",
}
LOCAL_NETWORK_CLASSES = {"residential_isp", "mobile_carrier", "business_isp"}
VALID_REVIEW = {"PENDING", "APPROVED", "REJECTED"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def artifact_errors(item: object, label: str, base: Path) -> list[str]:
    if not isinstance(item, dict):
        return [f"{label} must be an object"]
    errors = []
    path_value = item.get("evidence_file")
    digest = item.get("evidence_sha256")
    if not isinstance(path_value, str) or not path_value.strip():
        errors.append(f"{label}.evidence_file is required")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        errors.append(f"{label}.evidence_sha256 must be a lowercase SHA-256 digest")
    if isinstance(path_value, str) and path_value.strip() and isinstance(digest, str) and SHA256_RE.fullmatch(digest):
        raw = Path(path_value)
        path = raw if raw.is_absolute() else (base / raw).resolve()
        try:
            if not path.is_file():
                errors.append(f"{label}: evidence file not found: {path_value}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                errors.append(f"{label}: evidence SHA-256 mismatch: {path_value}")
        except OSError as exc:
            errors.append(f"{label}: cannot read evidence file: {exc}")
    return errors


def validate_attestation(record: object, base: Path) -> tuple[list[str], str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["attestation must be a JSON object"], "EVIDENCE_INCOMPLETE"
    extra = set(record) - ROOT_FIELDS
    if extra:
        errors.append("unexpected fields: " + ", ".join(sorted(extra)))
    missing = ROOT_FIELDS - set(record)
    if missing:
        errors.append("missing fields: " + ", ".join(sorted(missing)))
        return errors, "EVIDENCE_INCOMPLETE"
    if record.get("schema") != SCHEMA:
        errors.append("unexpected schema identifier")
    for field in ("attestation_id", "country_code", "interface_locale"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if record.get("country_code") != "RU":
        errors.append("this attestation profile is specifically for the RU baseline")
    if record.get("interface_locale") != "ru-RU":
        errors.append("RU baseline interface_locale must be ru-RU")
    observed_at = parse_time(record.get("observed_at_utc"))
    if observed_at is None:
        errors.append("observed_at_utc must be an ISO-8601 UTC timestamp")

    network = record.get("network")
    if not isinstance(network, dict):
        errors.append("network must be an object")
        network = {}
    allowed_network_fields = {"connection_type", "vpn_detected", "proxy_detected", "remote_desktop_detected", "ip_fingerprint_sha256", "provider_name", "asn"}
    if set(network) - allowed_network_fields:
        errors.append("network contains unsupported fields; raw IP addresses and credentials must never be stored")
    allowed_network = LOCAL_NETWORK_CLASSES | {"vpn", "proxy", "cloud_hosting", "remote_desktop", "unknown"}
    connection = network.get("connection_type")
    if connection not in allowed_network:
        errors.append("network.connection_type is invalid")
    for field in ("vpn_detected", "proxy_detected", "remote_desktop_detected"):
        if not isinstance(network.get(field), bool):
            errors.append(f"network.{field} must be boolean")
    fingerprint = network.get("ip_fingerprint_sha256")
    if not isinstance(fingerprint, str) or not SHA256_RE.fullmatch(fingerprint):
        errors.append("network.ip_fingerprint_sha256 must be a SHA-256 fingerprint; raw IP addresses must not be stored")
    if not isinstance(network.get("provider_name"), str) or not network.get("provider_name", "").strip():
        errors.append("network.provider_name is required")
    if connection not in LOCAL_NETWORK_CLASSES:
        errors.append("network connection is not an eligible direct local ISP/mobile/business connection")
    for field in ("vpn_detected", "proxy_detected", "remote_desktop_detected"):
        if network.get(field) is not False:
            errors.append(f"network.{field} must be false for the RU baseline")

    geo = record.get("geolocation_sources")
    geo_times = []
    if not isinstance(geo, list) or len(geo) < 2:
        errors.append("geolocation_sources requires at least two independent sources")
        geo = []
    independence = set()
    providers = set()
    for index, source in enumerate(geo, start=1):
        label = f"geolocation_sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        allowed_source_fields = {"provider", "independence_group", "country_code", "captured_at_utc", "evidence_file", "evidence_sha256"}
        if set(source) - allowed_source_fields:
            errors.append(f"{label} contains unsupported fields")
        for field in ("provider", "independence_group", "country_code", "captured_at_utc"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                errors.append(f"{label}.{field} is required")
        if source.get("country_code") != "RU":
            errors.append(f"{label}.country_code must be RU")
        independence.add(source.get("independence_group"))
        providers.add(source.get("provider"))
        timestamp = parse_time(source.get("captured_at_utc"))
        if timestamp is None:
            errors.append(f"{label}.captured_at_utc must be ISO-8601 UTC")
        else:
            geo_times.append(timestamp)
        errors.extend(artifact_errors(source, label, base))
    if len(independence) < 2:
        errors.append("geolocation sources must have at least two distinct independence_group values")
    if len(providers) < 2:
        errors.append("geolocation sources must name at least two distinct providers")

    owner = record.get("network_owner_evidence")
    errors.extend(artifact_errors(owner, "network_owner_evidence", base))
    if isinstance(owner, dict):
        allowed_owner_fields = {"provider", "organization", "network_class", "evidence_file", "evidence_sha256"}
        if set(owner) - allowed_owner_fields:
            errors.append("network_owner_evidence contains unsupported fields")
        if owner.get("network_class") not in LOCAL_NETWORK_CLASSES:
            errors.append("network_owner_evidence.network_class must identify a local ISP, mobile carrier or business ISP")
        if not isinstance(owner.get("organization"), str) or not owner.get("organization", "").strip():
            errors.append("network_owner_evidence.organization is required")
        if not isinstance(owner.get("provider"), str) or not owner.get("provider", "").strip():
            errors.append("network_owner_evidence.provider is required")
        if owner.get("network_class") != connection:
            errors.append("network_owner_evidence.network_class must match network.connection_type")

    session = record.get("session_capture")
    errors.extend(artifact_errors(session, "session_capture", base))
    if isinstance(session, dict):
        allowed_session_fields = {"platform", "product", "interface_locale", "captured_at_utc", "evidence_file", "evidence_sha256"}
        if set(session) - allowed_session_fields:
            errors.append("session_capture contains unsupported fields")
        for field in ("platform", "product", "interface_locale", "captured_at_utc"):
            if not isinstance(session.get(field), str) or not session[field].strip():
                errors.append(f"session_capture.{field} is required")
        if session.get("interface_locale") != "ru-RU":
            errors.append("session_capture.interface_locale must be ru-RU")
        session_time = parse_time(session.get("captured_at_utc"))
        if session_time is None:
            errors.append("session_capture.captured_at_utc must be ISO-8601 UTC")
        elif observed_at and abs((session_time - observed_at).total_seconds()) > 1800:
            errors.append("session capture must be within 30 minutes of the attestation timestamp")
        if session_time and geo_times and any(abs((item - session_time).total_seconds()) > 1800 for item in geo_times):
            errors.append("geolocation evidence must be within 30 minutes of the session capture")

    declaration = record.get("operator_declaration")
    if not isinstance(declaration, dict):
        errors.append("operator_declaration must be an object")
    else:
        allowed_declaration_fields = {"operator", "direct_connection", "no_vpn", "no_proxy", "no_remote_desktop"}
        if set(declaration) - allowed_declaration_fields:
            errors.append("operator_declaration contains unsupported fields")
        if not isinstance(declaration.get("operator"), str) or not declaration.get("operator", "").strip():
            errors.append("operator_declaration.operator is required")
        for field in ("direct_connection", "no_vpn", "no_proxy", "no_remote_desktop"):
            if declaration.get(field) is not True:
                errors.append(f"operator_declaration.{field} must be explicitly true")

    review = record.get("review")
    if not isinstance(review, dict):
        errors.append("review must be an object")
        review = {}
    allowed_review_fields = {"status", "reviewer", "reviewed_at_utc", "rationale"}
    if set(review) - allowed_review_fields:
        errors.append("review contains unsupported fields")
    review_status = review.get("status")
    if review_status not in VALID_REVIEW:
        errors.append("review.status must be PENDING, APPROVED or REJECTED")
    if review_status in {"APPROVED", "REJECTED"}:
        if not isinstance(review.get("reviewer"), str) or not review.get("reviewer", "").strip():
            errors.append("review decision requires reviewer")
        if review.get("reviewer") == (declaration.get("operator") if isinstance(declaration, dict) else None):
            errors.append("reviewer must be independent from the operator")
        reviewed_at = parse_time(review.get("reviewed_at_utc"))
        if reviewed_at is None:
            errors.append("review decision requires reviewed_at_utc")
        elif observed_at and reviewed_at < observed_at:
            errors.append("reviewed_at_utc cannot precede the attestation")
        if not isinstance(review.get("rationale"), str) or not review.get("rationale", "").strip():
            errors.append("review decision requires a rationale")

    if errors:
        return errors, "EVIDENCE_INCOMPLETE"
    if review_status == "REJECTED":
        return [], "REJECTED"
    if review_status != "APPROVED":
        return [], "PENDING_REVIEW"
    return [], "VERIFIED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attestation", type=Path)
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.attestation.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read attestation: {exc}", file=sys.stderr)
        return 2
    errors, status = validate_attestation(record, args.attestation.resolve().parent)
    print(f"REGION ATTESTATION STATUS: {status}")
    if errors:
        for error in errors:
            print(f" - {error}")
        return 1
    print("Structural and artifact-integrity checks passed.")
    print("This validator does not independently prove physical location or source truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
