#!/usr/bin/env python3
"""Validate a recent official-site Search Console snapshot without attributing it to legacy GEO URLs."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "ops/ai-discoverability/RECENT_SERVICE_ROUTE_SEARCHCONSOLE_OBSERVATION.json"
ROUTES = ROOT / "ops/ai-discoverability/SERVICE_ROUTE_REGISTRY.json"

def validate(data: Any, routes_data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["snapshot must be an object"]
    if data.get("schema") != "studio/official-service-route-searchconsole-snapshot/1":
        errors.append("unexpected snapshot schema")
    source = data.get("source")
    if not isinstance(source, dict):
        return errors + ["source must be an object"]
    if source.get("product") != "Google Search Console":
        errors.append("source product must be Google Search Console")
    if source.get("property") != "https://www.audio-reclama.ru/":
        errors.append("snapshot property differs from the selected official-site property")
    if (source.get("date_from"), source.get("date_to"), source.get("calendar_days")) != ("2026-10-22", "2026-11-17", 27):
        errors.append("snapshot date range must remain the observed 27-day window")
    if source.get("include_fresh_data") is not False:
        errors.append("unfinalized fresh data must remain excluded")
    if source.get("page_level_rows") != 10 or source.get("query_level_rows") != 122:
        errors.append("observed row counts must remain 10 page rows and 122 query rows")
    if source.get("selected_query_rows") != len(data.get("query_level", {}).get("selected_rows", [])):
        errors.append("selected query sample count does not reconcile")
    long_range = source.get("long_range_attempt", {})
    if long_range.get("status") != "blocked_by_current_trial_history_limit":
        errors.append("older data-access limitation must remain explicit")
    policy = data.get("policy", {})
    if policy.get("no_paid_upgrade_or_spend") is not True:
        errors.append("no-paid-upgrade policy must remain true")
    if not isinstance(routes_data, dict):
        return errors + ["service route registry must be an object"]
    route_map = {x.get("id"): x for x in routes_data.get("routes", []) if isinstance(x, dict)}
    expected_ids = {rid for rid, row in route_map.items() if row.get("route_kind") == "professional_service"}
    rows = data.get("pages")
    if not isinstance(rows, list) or len(rows) != 10:
        return errors + ["pages must contain exactly ten professional-service rows"]
    seen: set[str] = set()
    clicks = 0
    impressions = 0
    for index, row in enumerate(rows):
        rid = row.get("route_id") if isinstance(row, dict) else None
        prefix = f'pages[{index}]'
        if not isinstance(rid, str) or not rid:
            errors.append(f"{prefix}.route_id is required")
            continue
        if rid in seen:
            errors.append(f"duplicate route_id: {rid}")
        seen.add(rid)
        canonical = route_map.get(rid)
        if canonical is None or canonical.get('route_kind') != 'professional_service':
            errors.append(f"{prefix}: route_id is not a professional service route")
        elif row.get('url') != canonical.get('destination_url'):
            errors.append(f"{prefix}: URL differs from SERVICE_ROUTE_REGISTRY")
        for metric in ("clicks", "impressions"):
            if not isinstance(row.get(metric), int) or row[metric] < 0:
                errors.append(f"{prefix}.{metric} must be a non-negative integer")
        for metric in ('ctr', 'average_position'):
            if not isinstance(row.get(metric), (int, float)) or row[metric] < 0:
                errors.append(f"{prefix}.{metric} must be a non-negative number")
        clicks += row.get('clicks', 0) if isinstance(row.get('clicks'), int) else 0
        impressions += row.get('impressions', 0) if isinstance(row.get('impressions'), int) else 0
    if seen != expected_ids:
        errors.append("snapshot must cover exactly the professional_service routes")
    totals = data.get('page_level_totals', {})
    if totals.get('pages') != len(rows) or totals.get('clicks') != clicks or totals.get('impressions') != impressions:
        errors.append("page_level_totals do not reconcile with page rows")
    expected_ctr = clicks / impressions if impressions else 0
    if abs(totals.get('weighted_ctr', -1) - expected_ctr) > 0.000001:
        errors.append("weighted CTR does not reconcile with page totals")
    scope = data.get('scope', {})
    if scope.get('route_metrics_do_not_measure_legacy_answer_url_performance') is not True:
        errors.append("official route metrics must not be attributed to legacy answer URLs")
    ga4 = data.get('cross_source_check', {})
    if ga4.get('status') != 'done_empty_response' or ga4.get('rows') != 0:
        errors.append("GA4 empty response status must be preserved")
    if "not evidence of zero traffic" not in ga4.get("interpretation", ""):
        errors.append("GA4 empty response must not be interpreted as zero traffic")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.parse_args()
    try:
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read Search Console snapshot or service route registry: {exc}")
        return 1
    errors = validate(data, routes)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: Search Console snapshot reconciles to ten official service routes; legacy URL and GA4 zero-traffic inferences are blocked")
    return 0

if __name__ == "__main__":
    sys.exit(main())
