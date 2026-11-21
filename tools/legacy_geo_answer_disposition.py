#!/usr/bin/env python3
"""Offline validation for the seven-page legacy GEO disposition matrix."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/"ops/ai-discoverability/LEGACY_ANSWER_DISPOSITION.json"
PROVENANCE=ROOT/"ops/ai-discoverability/LEGACY_ANSWER_PROVENANCE.json"
ROUTES=ROOT/"ops/ai-discoverability/SERVICE_ROUTE_REGISTRY.json"

ALLOWED_DISPOSITIONS={
 "retain_url_rewrite_as_qualified_short_order_or_project_router",
 "retain_url_rewrite_to_professional_presentation_route",
 "retain_url_rewrite_as_explicit_product_vs_project_split",
 "retain_url_rewrite_as_medium_and_buyer_qualifier",
 "retain_url_rewrite_as_two_buyer_paths",
 "retain_url_hold_consolidation_until_query_and_referral_evidence",
 "retain_url_rewrite_as_scope_qualifier_no_generic_fixed_price",
}
ALLOWED_REDIRECT={"not_recommended_now","defer_until_page_level_search_and_referral_evidence"}


def validate(data:Any,provenance:Any,routes:Any)->list[str]:
 errors=[]
 if not isinstance(data,dict): return ["disposition matrix must be an object"]
 if data.get("schema")!="studio/legacy-geo-answer-disposition/1": errors.append("unexpected matrix schema")
 pol=data.get("policy")
 if not isinstance(pol,dict): errors.append("policy must be an object")
 else:
  for key in ("official_site_is_read_only","geo_static_output_is_read_only"):
   if pol.get(key) is not True: errors.append(f"policy.{key} must remain true")
  for key in ("external_publication_authorized","github_pages_deployment_authorized","redirect_or_retirement_authorized","current_audio_plus_contractual_terms_confirmed","page_level_traffic_and_referral_evidence_available"):
   if pol.get(key) is not False: errors.append(f"policy.{key} must remain false")
 if not isinstance(provenance,dict) or not isinstance(routes,dict):
  return errors+["source provenance or route registry is invalid"]
 legacy={x.get("slug"):x for x in provenance.get("legacy_pages",[]) if isinstance(x,dict)}
 route_ids={x.get("id") for x in routes.get("routes",[]) if isinstance(x,dict)}
 if "audio_plus_short_order" not in {x.get("id") for x in routes.get("product_boundaries",[]) if isinstance(x,dict)}:
  errors.append("Audio+ short-order product boundary is missing from the route registry")
 pages=data.get("pages")
 if not isinstance(pages,list): return errors+["pages must be an array"]
 seen=set()
 for i,page in enumerate(pages):
  p=f"pages[{i}]"
  if not isinstance(page,dict): errors.append(f"{p} must be an object"); continue
  slug=page.get("slug")
  if not isinstance(slug,str) or not slug: errors.append(f"{p}.slug is required"); continue
  if slug in seen: errors.append(f"duplicate disposition slug: {slug}")
  seen.add(slug)
  source=legacy.get(slug)
  if source is None: errors.append(f"{p}: slug is not a registered legacy page")
  elif page.get("repository_path")!=source.get("path"): errors.append(f"{p}: repository path differs from provenance registry")
  if page.get("recommended_disposition") not in ALLOWED_DISPOSITIONS: errors.append(f"{p}.recommended_disposition is invalid")
  if page.get("redirect_or_retire") not in ALLOWED_REDIRECT: errors.append(f"{p}.redirect_or_retire must defer irreversible action")
  if not isinstance(page.get("recommended_next_content"),str) or len(page["recommended_next_content"])<30: errors.append(f"{p}.recommended_next_content is too short")
  if not isinstance(page.get("required_before_public_edit"),list) or not page["required_before_public_edit"]: errors.append(f"{p}.required_before_public_edit is required")
  route_list=page.get("professional_route_ids")
  if not isinstance(route_list,list) or any(rid not in route_ids for rid in route_list): errors.append(f"{p}.professional_route_ids contains unknown route ids")
  if not isinstance(page.get("audio_plus_path"),str) or not page["audio_plus_path"]: errors.append(f"{p}.audio_plus_path must preserve eligibility gate")
  if not isinstance(page.get("rationale"),str) or not page["rationale"]: errors.append(f"{p}.rationale is required")
  if page.get("recommended_disposition")=="retain_url_hold_consolidation_until_query_and_referral_evidence" and not any("Search Console" in x or "page-level" in x for x in page.get("required_before_public_edit",[])):
   errors.append(f"{p}: consolidation must require page-level performance evidence")
 if seen!=set(legacy):
  errors.append("disposition pages must cover exactly all legacy pages: "+", ".join(sorted(set(legacy)^seen)))
 sf=data.get("source_freshness")
 if not isinstance(sf,dict): errors.append("source_freshness must be an object")
 else:
  for key in ("product_homepage","offer"):
   row=sf.get(key)
   if not isinstance(row,dict) or not row.get("search_index_age") or not row.get("opened_page_age"):
    errors.append(f"source_freshness.{key} must preserve both search and opened-page ages")
  if sf.get("offer",{}).get("visible_publication_date")!="2016-06-17": errors.append("offer publication date must remain visible")
  corr=sf.get("correction_terms")
  if not isinstance(corr,dict) or corr.get("status")!="interpretation_not_resolved":
   errors.append("790 ₽ correction/rework interpretation must remain unresolved")
  elif len(corr.get("dimensions",[]))<3: errors.append("correction terms must separate three distinct operations")
  scope=sf.get("scope_difference")
  if not isinstance(scope,dict) or scope.get("status")!="not_fully_reconciled": errors.append("Audio+ video scope difference must remain unresolved")
  obs=sf.get("source_observations")
  if not isinstance(obs,list) or len(obs)<5: errors.append("source observations must include Audio+ and professional primary pages")
  else:
   for o in obs:
    if not isinstance(o,dict) or not o.get("source") or not o.get("retrieval") or not o.get("reported_crawl_age"):
     errors.append("every source observation must preserve URL, retrieval mode and crawl age")
 if seen and data.get("summary",{}).get("recommended_immediate_redirects")!=0:
  errors.append("no immediate redirect may be recommended in this evidence state")
 if data.get("summary",{}).get("page_count")!=len(pages): errors.append("summary page_count mismatch")
 if data.get("summary",{}).get("recommended_keep_urls")!=len(pages): errors.append("all seven URLs must be recommended stable for now")
 principles=data.get("disposition_principles")
 if not isinstance(principles,list) or not any("do not" in x.lower() and "delete" in x.lower() for x in principles):
  errors.append("disposition principles must preserve the no-delete guardrail")
 return errors


def main()->int:
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("command",choices=["validate"]);parser.parse_args()
 try:
  data=json.loads(MATRIX.read_text(encoding="utf-8"))
  provenance=json.loads(PROVENANCE.read_text(encoding="utf-8"))
  routes=json.loads(ROUTES.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError) as exc:
  print(f"FAIL: cannot read disposition inputs: {exc}");return 1
 errors=validate(data,provenance,routes)
 if errors:
  for item in errors: print("FAIL:",item)
  return 1
 print("PASS: all seven legacy URLs have source-backed conservative dispositions; redirects and publication remain gated")
 return 0


if __name__=="__main__": sys.exit(main())
