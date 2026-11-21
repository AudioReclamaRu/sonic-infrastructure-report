#!/usr/bin/env python3
"""Offline validation for the professional service-route evidence matrix."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "ops/ai-discoverability/SERVICE_ROUTE_EVIDENCE_MATRIX.json"
ROUTES = ROOT / "ops/ai-discoverability/SERVICE_ROUTE_REGISTRY.json"
ALLOWED_RESULTS = {"cached_snapshot", "indexed_excerpt", "cache_miss"}
ALLOWED_MODES = {"opened_page_snapshot", "search_index_result"}
ALLOWED_FRESHNESS = {
    "aged_snapshot_only",
    "old_snapshot_only",
    "mixed_age_observations",
    "recent_index_with_direct_cache_miss",
    "aged_index_with_direct_cache_miss",
    "mixed_recent_and_aged_observations",
}


def validate_matrix(data: Any, route_data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["evidence matrix must be an object"]
    if data.get("schema") != "studio/service-route-evidence-matrix/1":
        errors.append("unexpected evidence matrix schema")

    policy = data.get("policy")
    expected_false = (
        "external_publication_authorized",
        "github_pages_deployment_authorized",
        "route_links_live_checked",
        "live_http_status_checked",
        "current_service_scope_confirmed",
        "current_commercial_terms_confirmed",
        "current_rights_terms_confirmed",
    )
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        if policy.get("official_site_is_read_only") is not True:
            errors.append("official_site_is_read_only must remain true")
        for key in expected_false:
            if policy.get(key) is not False:
                errors.append(f"policy.{key} must remain false")

    method = data.get("method")
    if not isinstance(method, dict):
        errors.append("method must be an object")
    else:
        for key in ("source_set", "retrieval", "crawl_age_rule", "cache_miss_rule", "claim_rule"):
            if not isinstance(method.get(key), str) or not method[key].strip():
                errors.append(f"method.{key} must be non-empty text")
        if not isinstance(method.get("exclusions"), list) or not method["exclusions"]:
            errors.append("method.exclusions must be a non-empty array")

    if not isinstance(route_data, dict):
        return errors + ["service route registry must be an object"]
    route_map = {
        route.get("id"): route for route in route_data.get("routes", [])
        if isinstance(route, dict) and route.get("route_kind") == "professional_service"
    }
    matrix_routes = data.get("routes")
    if not isinstance(matrix_routes, list):
        return errors + ["routes must be an array"]

    expected_ids = set(route_map)
    seen: set[str] = set()
    for index, route in enumerate(matrix_routes):
        prefix = f"routes[{index}]"
        if not isinstance(route, dict):
            errors.append(f"{prefix} must be an object")
            continue
        route_id = route.get("route_registry_id")
        if not isinstance(route_id, str) or not route_id.strip():
            errors.append(f"{prefix}.route_registry_id must be non-empty")
            continue
        if route_id in seen:
            errors.append(f"duplicate route evidence id: {route_id}")
        seen.add(route_id)
        canonical = route_map.get(route_id)
        if canonical is None:
            errors.append(f"{prefix}: route_registry_id is not a professional route")
        elif route.get("destination_url") != canonical.get("destination_url"):
            errors.append(f"{prefix}: destination differs from SERVICE_ROUTE_REGISTRY")

        for key in ("page_title", "freshness_class", "rights_observation", "recommended_refresh"):
            if not isinstance(route.get(key), str) or not route[key].strip():
                errors.append(f"{prefix}.{key} must be non-empty text")
        if route.get("freshness_class") not in ALLOWED_FRESHNESS:
            errors.append(f"{prefix}.freshness_class is invalid")
        for key in ("observed_scope", "scope_limits"):
            if not isinstance(route.get(key), list) or not route[key] or any(not isinstance(x, str) or not x.strip() for x in route[key]):
                errors.append(f"{prefix}.{key} must be a non-empty text array")

        if route.get("service_presence_status") != "observed_in_source_snapshot":
            errors.append(f"{prefix}: service presence must remain snapshot-based")
        if route.get("current_service_scope_confirmed") is not False:
            errors.append(f"{prefix}: current service scope must remain unconfirmed")
        if route.get("current_commercial_terms_confirmed") is not False:
            errors.append(f"{prefix}: current commercial terms must remain unconfirmed")
        if route.get("current_rights_terms_confirmed") is not False:
            errors.append(f"{prefix}: current rights terms must remain unconfirmed")
        if route.get("live_http_status") != "not_tested":
            errors.append(f"{prefix}: live HTTP status must remain NOT_TESTED")
        if route.get("form_submission_status") != "not_tested":
            errors.append(f"{prefix}: form submission must remain NOT_TESTED")
        priority = route.get("refresh_priority")
        if priority not in {"high", "medium", "low"}:
            errors.append(f"{prefix}.refresh_priority is invalid")

        observations = route.get("source_observations")
        if not isinstance(observations, list) or not observations:
            errors.append(f"{prefix}.source_observations must be non-empty")
            continue
        for obs_index, obs in enumerate(observations):
            op = f"{prefix}.source_observations[{obs_index}]"
            if not isinstance(obs, dict):
                errors.append(f"{op} must be an object")
                continue
            if obs.get("source_url") != route.get("destination_url"):
                errors.append(f"{op}: source_url must match the route destination")
            if obs.get("retrieval_mode") not in ALLOWED_MODES:
                errors.append(f"{op}.retrieval_mode is invalid")
            if obs.get("retrieval_result") not in ALLOWED_RESULTS:
                errors.append(f"{op}.retrieval_result is invalid")
            if not isinstance(obs.get("captured_on"), str) or not obs["captured_on"]:
                errors.append(f"{op}.captured_on is required")
            if not isinstance(obs.get("note"), str) or not obs["note"].strip():
                errors.append(f"{op}.note is required")
            age = obs.get("reported_crawl_age")
            if obs.get("retrieval_result") == "cache_miss" and age is not None:
                errors.append(f"{op}: cache miss must not carry a crawl age")
            elif obs.get("retrieval_result") != "cache_miss" and (not isinstance(age, str) or not age.strip()):
                errors.append(f"{op}: retrieved snapshot must retain its reported crawl age")

    missing_ids = sorted(expected_ids - seen)
    extra_ids = sorted(seen - expected_ids)
    if missing_ids:
        errors.append("professional service routes missing from evidence matrix: " + ", ".join(missing_ids))
    if extra_ids:
        errors.append("unknown professional route evidence ids: " + ", ".join(extra_ids))
    coverage = data.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("coverage must be an object")
    else:
        if coverage.get("professional_service_routes_expected") != len(expected_ids):
            errors.append("coverage expected count differs from SERVICE_ROUTE_REGISTRY")
        if coverage.get("professional_service_routes_observed") != len(matrix_routes):
            errors.append("coverage observed count differs from matrix route count")
        if coverage.get("voice_discovery_general_intake_and_case_reference_excluded") is not True:
            errors.append("non-professional route classes must remain explicitly excluded")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.parse_args()
    try:
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read evidence matrix or service registry: {exc}")
        return 1
    errors = validate_matrix(matrix, routes)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: all professional routes have source-freshness and claim-boundary evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
