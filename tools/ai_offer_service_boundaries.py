#!/usr/bin/env python3
"""Offline validation for Audio+ product vs professional-service evidence boundaries."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = ROOT / "ops/ai-discoverability/OFFER_SERVICE_BOUNDARIES.json"
ROUTES = ROOT / "ops/ai-discoverability/SERVICE_ROUTE_REGISTRY.json"


def _read(path: Path) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{path.relative_to(ROOT)}: cannot read valid JSON: {exc}"]


def validate_boundaries(data: Any, routes_data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["boundary registry must be an object"]
    if data.get("schema") != "studio/offer-service-boundary-registry/1":
        errors.append("unexpected boundary registry schema")

    policy = data.get("policy")
    expected_policy = {
        "official_site_is_read_only": True,
        "external_publication_authorized": False,
        "github_pages_deployment_authorized": False,
        "current_terms_confirmed": False,
        "source_snapshot_freshness_must_be_preserved": True,
    }
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        for field, expected in expected_policy.items():
            if policy.get(field) is not expected:
                errors.append(f"policy.{field} must remain {expected}")

    products = data.get("products")
    if not isinstance(products, list) or not products:
        return errors + ["products must be a non-empty array"]
    product_ids: set[str] = set()
    for i, product in enumerate(products):
        prefix = f"products[{i}]"
        if not isinstance(product, dict):
            errors.append(f"{prefix} must be an object")
            continue
        pid = product.get("id")
        if not isinstance(pid, str) or not pid.strip():
            errors.append(f"{prefix}.id must be non-empty")
        elif pid in product_ids:
            errors.append(f"duplicate product id: {pid}")
        else:
            product_ids.add(pid)
        if product.get("entity_type") != "short_order_product":
            errors.append(f"{prefix}: Audio+ must remain a short_order_product")
        audience = product.get("audience")
        if not isinstance(audience, dict):
            errors.append(f"{prefix}.audience must be an object")
        else:
            statement = audience.get("observed_statement", "").lower()
            if "не предназначен для юридических лиц" not in statement or not ("ип" in statement or "индивидуальных предпринимателей" in statement):
                errors.append(f"{prefix}: exact buyer-eligibility observation is missing")
            if audience.get("source_status") != "stale_official_snapshot":
                errors.append(f"{prefix}: stale offer snapshot must not be relabelled as fresh")
            if audience.get("current_eligibility_confirmed") is not False:
                errors.append(f"{prefix}: current buyer eligibility is not confirmed")

        revisions = product.get("revisions")
        if not isinstance(revisions, dict) or revisions.get("status") != "unresolved_source_conflict":
            errors.append(f"{prefix}: edit/rework conflict must remain explicitly unresolved")
        elif revisions.get("current_revision_terms_confirmed") is not False:
            errors.append(f"{prefix}: revision terms cannot be marked confirmed")

        rights = product.get("rights")
        if not isinstance(rights, dict):
            errors.append(f"{prefix}.rights must be an object")
        else:
            if rights.get("observed_exclusive_right_holder") != "service":
                errors.append(f"{prefix}: Audio+ offer snapshot must preserve the stated exclusive-right holder")
            if rights.get("observed_customer_permission") != "simple_non_exclusive_license_with_sublicensing_right_as_worded_in_the_offer":
                errors.append(f"{prefix}: non-exclusive licence observation must remain distinct")
            if rights.get("current_rights_terms_confirmed") is not False:
                errors.append(f"{prefix}: current rights terms must remain unconfirmed")

        price_status = product.get("price_status")
        if not isinstance(price_status, dict) or price_status.get("current_price_confirmed") is not False:
            errors.append(f"{prefix}: current price must remain unconfirmed")

    professional = data.get("professional_service_examples")
    if not isinstance(professional, list) or not professional:
        errors.append("professional_service_examples must be a non-empty array")
        return errors
    if not isinstance(routes_data, dict):
        return errors + ["service route registry must be an object"]
    route_by_id = {
        r.get("id"): r for r in routes_data.get("routes", [])
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    seen_services: set[str] = set()
    for i, service in enumerate(professional):
        prefix = f"professional_service_examples[{i}]"
        if not isinstance(service, dict):
            errors.append(f"{prefix} must be an object")
            continue
        sid = service.get("id")
        if not isinstance(sid, str) or not sid or sid in seen_services:
            errors.append(f"{prefix}: service id must be unique and non-empty")
        else:
            seen_services.add(sid)
        if service.get("entity_type") != "professional_project_service":
            errors.append(f"{prefix}: professional route must be classified as a project service")
        route_id = service.get("route_registry_id")
        route = route_by_id.get(route_id)
        if route is None:
            errors.append(f"{prefix}: route_registry_id is not in SERVICE_ROUTE_REGISTRY")
        else:
            if route.get("route_kind") != "professional_service":
                errors.append(f"{prefix}: referenced route is not a professional_service")
            if service.get("destination_url") != route.get("destination_url"):
                errors.append(f"{prefix}: destination differs from SERVICE_ROUTE_REGISTRY")
        rights = service.get("rights")
        if not isinstance(rights, dict):
            errors.append(f"{prefix}.rights must be explicit")
        elif sid == "radio_advertising_production":
            if rights.get("observed_page_statement") != "transfer of author's and exclusive rights is listed among the service elements":
                errors.append(f"{prefix}: observed page-level rights wording missing")
            if rights.get("current_contract_scope_confirmed") is not False:
                errors.append(f"{prefix}: service-page wording must not be promoted into confirmed contract scope")
        elif rights.get("status") != "not_established_by_the_inspected_page_snapshot":
            errors.append(f"{prefix}: unverified professional rights must remain not established")

    rules = data.get("non_equivalence_rules")
    required_rules = [
        "A short-order Audio+ product is not a default destination or price basis for professional project routes.",
        "Individual-buyer eligibility, a one-file workflow and short text limits must not be silently generalised to business project scopes.",
        "A non-exclusive licence model must not be replaced by an exclusive-right transfer statement; the reverse transfer is also prohibited without source evidence.",
        "The product-page edit option and offer restrictions on changes/rework remain an unresolved source conflict."
    ]
    if not isinstance(rules, list):
        errors.append("non_equivalence_rules must be an array")
    else:
        for rule in required_rules:
            if rule not in rules:
                errors.append(f"missing non-equivalence safeguard: {rule}")

    if data.get("linked_registry") != "ops/ai-discoverability/SERVICE_ROUTE_REGISTRY.json":
        errors.append("boundary registry must link the existing service route registry")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.parse_args()
    data, errors = _read(BOUNDARIES)
    routes, route_errors = _read(ROUTES)
    errors.extend(route_errors)
    if data is not None and routes is not None:
        errors.extend(validate_boundaries(data, routes))
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: product eligibility, fulfillment, revision and rights boundaries remain explicit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
