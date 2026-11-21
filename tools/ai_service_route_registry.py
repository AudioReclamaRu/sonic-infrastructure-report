#!/usr/bin/env python3
"""Validate internal buyer-guide to official-service route mappings (offline only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ops/ai-discoverability/SERVICE_ROUTE_REGISTRY.json"
CANONICAL_HOST = "www.audio-reclama.ru"
ROUTE_KINDS = {
    "voice_discovery",
    "general_intake",
    "professional_service",
    "case_reference",
}
AUDIENCE_CLASSES = {
    "voice_selection",
    "general_intake",
    "professional_project",
    "proof_reference",
}
PRODUCT_ROUTE_MARKERS = ("audio.plus", "/audioplus/")


def validate_registry(data: Any, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["route registry must be an object"]
    if data.get("schema") != "studio/service-route-registry/1":
        errors.append("unexpected service-route registry schema")

    policy = data.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        expected_policy = {
            "official_site_is_read_only": True,
            "external_publication_authorized": False,
            "github_pages_deployment_authorized": False,
            "route_links_are_live_checked": False,
        }
        for field, expected in expected_policy.items():
            if policy.get(field) is not expected:
                errors.append(f"policy.{field} has an unsafe or unsupported value")

    routes = data.get("routes")
    if not isinstance(routes, list) or not routes:
        return errors + ["routes must be a non-empty array"]

    seen_ids: set[str] = set()
    root_path = Path(root).resolve()
    for index, route in enumerate(routes):
        prefix = f"routes[{index}]"
        if not isinstance(route, dict):
            errors.append(f"{prefix} must be an object")
            continue

        route_id = route.get("id")
        if not isinstance(route_id, str) or not route_id.strip():
            errors.append(f"{prefix}.id must be non-empty text")
        elif route_id in seen_ids:
            errors.append(f"duplicate route id: {route_id}")
        else:
            seen_ids.add(route_id)

        for field in ("task", "route_kind", "audience_class", "destination_url", "link_role", "scope_note"):
            if not isinstance(route.get(field), str) or not route[field].strip():
                errors.append(f"{prefix}.{field} must be non-empty text")
        if route.get("route_kind") not in ROUTE_KINDS:
            errors.append(f"{prefix}.route_kind is invalid")
        if route.get("audience_class") not in AUDIENCE_CLASSES:
            errors.append(f"{prefix}.audience_class is invalid")

        destination = route.get("destination_url")
        if isinstance(destination, str) and destination.strip():
            parsed = urlsplit(destination)
            if parsed.scheme != "https" or parsed.netloc != CANONICAL_HOST:
                errors.append(f"{prefix}.destination_url must use the canonical HTTPS host")
            if parsed.query or parsed.fragment:
                errors.append(f"{prefix}.destination_url must be a stable URL without query or fragment")
            if parsed.path == "/" and destination.endswith("/"):
                errors.append(f"{prefix}.destination_url root URL must not have a trailing slash")

        if route.get("route_kind") == "professional_service":
            if route.get("audience_class") != "professional_project":
                errors.append(f"{prefix}: professional service must use professional_project audience class")
            if isinstance(destination, str) and any(marker in destination.lower() for marker in PRODUCT_ROUTE_MARKERS):
                errors.append(f"{prefix}: a professional project route cannot default to the separate Audio+ short-order product")

        source_guides = route.get("source_guides")
        if not isinstance(source_guides, list) or not source_guides:
            errors.append(f"{prefix}.source_guides must be a non-empty array")
            continue

        valid_sources: list[str] = []
        for source in source_guides:
            if not isinstance(source, str) or not source.strip():
                errors.append(f"{prefix}.source_guides contains an invalid path")
                continue
            if source in valid_sources:
                errors.append(f"{prefix}.source_guides contains a duplicate path: {source}")
            else:
                valid_sources.append(source)

        matched = False
        for source in valid_sources:
            relative = Path(source)
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(f"{prefix}.source_guides contains an unsafe path: {source}")
                continue
            candidate = (root_path / relative).resolve()
            try:
                candidate.relative_to(root_path)
            except ValueError:
                errors.append(f"{prefix}.source_guides escapes the repository: {source}")
                continue
            if not candidate.is_file():
                errors.append(f"{prefix}: source guide not found: {source}")
                continue
            content = candidate.read_text(encoding="utf-8")
            if isinstance(destination, str) and destination in content:
                matched = True
        if not matched:
            errors.append(f"{prefix}: destination URL is not referenced in any listed source guide")

    boundaries = data.get("product_boundaries")
    if not isinstance(boundaries, list) or not boundaries:
        errors.append("product_boundaries must be a non-empty array")
        boundaries = []
    audio_plus_boundaries = [
        item for item in boundaries
        if isinstance(item, dict) and item.get("id") == "audio_plus_short_order"
    ]
    if not audio_plus_boundaries:
        errors.append("Audio+ short-order product boundary is missing")
    elif len(audio_plus_boundaries) > 1:
        errors.append("Audio+ short-order product boundary must be unique")
    else:
        boundary = audio_plus_boundaries[0]
        if boundary.get("destination_url") is not None:
            errors.append("Audio+ exclusion must not have a professional route destination")
        if boundary.get("professional_route_default") is not False:
            errors.append("Audio+ must not be a default professional-project route")
        if boundary.get("current_offer_recheck_required") is not True:
            errors.append("current offer must be rechecked before commercial wording changes")
        if boundary.get("evidence_status") != "saved_2026-11-20_offer_review_only_not_freshly_reverified":
            errors.append("offer evidence status must preserve its freshness limitation")

    return errors


def load_registry(path: Path = REGISTRY) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"cannot read route registry: {exc}"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.parse_args()
    data, errors = load_registry()
    if data is not None:
        errors.extend(validate_registry(data))
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: buyer-guide route links are consistent; public availability is not inferred")
    return 0


if __name__ == "__main__":
    sys.exit(main())
