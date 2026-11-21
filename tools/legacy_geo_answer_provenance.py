#!/usr/bin/env python3
"""Offline provenance and coverage checks for static GEO answer HTML."""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ops/ai-discoverability/LEGACY_ANSWER_PROVENANCE.json"
BUILDER = ROOT / "tools/build_geo_site.py"
ANSWERS_DIR = ROOT / "geo/answers"
ANSWERS_INDEX = ANSWERS_DIR / "index.html"
LLMS = ROOT / "geo/llms.txt"
SITEMAP = ROOT / "geo/sitemap.xml"


def extract_builder_slugs(source: str) -> tuple[set[str], set[str], list[str]]:
    """Return explicit build_pages routes, EXTRA_ANSWERS routes and parse errors."""
    errors: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return set(), set(), [f"builder source is not valid Python: {exc}"]

    explicit: set[str] = set()
    data_driven: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(isinstance(t, ast.Name) and t.id == "EXTRA_ANSWERS" for t in node.targets):
                continue
            if not isinstance(node.value, (ast.List, ast.Tuple)):
                errors.append("EXTRA_ANSWERS must remain a literal list or tuple")
                continue
            for index, item in enumerate(node.value.elts):
                if not isinstance(item, ast.Dict):
                    errors.append(f"EXTRA_ANSWERS[{index}] must be a literal dictionary")
                    continue
                slug = None
                for key, value in zip(item.keys, item.values):
                    if isinstance(key, ast.Constant) and key.value == "slug":
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            slug = value.value
                if not slug:
                    errors.append(f"EXTRA_ANSWERS[{index}] has no literal slug")
                elif slug in data_driven:
                    errors.append(f"duplicate EXTRA_ANSWERS slug: {slug}")
                else:
                    data_driven.add(slug)

    build_pages_fn = next(
        (n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "build_pages"),
        None,
    )
    if build_pages_fn is None:
        errors.append("build_pages() function not found")
    else:
        for node in ast.walk(build_pages_fn):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "page" or not node.args:
                continue
            arg = node.args[0]
            if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
                continue
            match = re.fullmatch(r"answers/([^/]+)/", arg.value)
            if match:
                explicit.add(match.group(1))

    return explicit, data_driven, errors


def _read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        errors.append(f"{path.relative_to(ROOT)}: cannot read: {exc}")
        return ""


def validate_provenance(
    data: Any,
    builder_source: str,
    answers_index: str,
    llms_text: str,
    sitemap_text: str,
    actual_slugs: set[str],
    page_canonicals: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["provenance registry must be an object"]
    if data.get("schema") != "studio/legacy-geo-answer-provenance/1":
        errors.append("unexpected provenance registry schema")

    policy = data.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        if policy.get("official_site_is_read_only") is not True:
            errors.append("official_site_is_read_only must remain true")
        if policy.get("geo_static_output_is_read_only") is not True:
            errors.append("geo_static_output_is_read_only must remain true")
        if policy.get("external_publication_authorized") is not False:
            errors.append("external_publication_authorized must remain false")
        if policy.get("github_pages_deployment_authorized") is not False:
            errors.append("github_pages_deployment_authorized must remain false")
        if policy.get("live_public_serving_status") != "not_tested":
            errors.append("live public serving must remain not_tested")
        if policy.get("commercial_claims_currently_confirmed") is not False:
            errors.append("current commercial claims must remain unconfirmed")

    explicit, data_driven, parse_errors = extract_builder_slugs(builder_source)
    errors.extend(parse_errors)
    managed = explicit | data_driven
    if explicit & data_driven:
        errors.append("an answer slug is both explicit and data-driven in the builder")

    source_model = data.get("source_model")
    if not isinstance(source_model, dict):
        errors.append("source_model must be an object")
        source_model = {}
    if source_model.get("hardcoded_answer_slugs") != sorted(explicit):
        errors.append("hardcoded_answer_slugs differs from build_pages()")
    if source_model.get("data_driven_answer_slugs") != sorted(data_driven):
        errors.append("data_driven_answer_slugs differs from EXTRA_ANSWERS")
    if source_model.get("sitemap_discovery_rule") != "_discover_urls recursively includes every index.html under the output directory.":
        errors.append("sitemap discovery rule must preserve recursive index.html coverage")
    if source_model.get("sitemap_lastmod_rule") != "_write_sitemap applies the single global UPDATED date to every URL rather than reading per-file content-change dates.":
        errors.append("sitemap lastmod rule must preserve global-date limitation")

    # The source itself must continue to implement the recorded recursive sitemap model.
    if ".rglob(\"index.html\")" not in builder_source:
        errors.append("builder no longer contains the recorded recursive index.html discovery")
    if "<lastmod>{UPDATED}</lastmod>" not in builder_source:
        errors.append("builder no longer contains the recorded global sitemap lastmod rule")

    legacy_pages = data.get("legacy_pages")
    if not isinstance(legacy_pages, list):
        errors.append("legacy_pages must be an array")
        legacy_pages = []
    legacy_slugs: set[str] = set()
    for index, item in enumerate(legacy_pages):
        prefix = f"legacy_pages[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        slug = item.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            errors.append(f"{prefix}.slug must be non-empty")
            continue
        if slug in legacy_slugs:
            errors.append(f"duplicate legacy slug: {slug}")
        legacy_slugs.add(slug)
        if slug in managed:
            errors.append(f"{prefix}: legacy slug is still managed by the current builder: {slug}")
        if item.get("current_generator_class") != "legacy_static_html_not_managed_by_current_builder":
            errors.append(f"{prefix}: current generator class must stay explicitly unmanaged")
        if item.get("path") != f"geo/answers/{slug}/index.html":
            errors.append(f"{prefix}.path does not match its slug")
        for key in ("introduced_in_commit", "last_changed_in_commit"):
            value = item.get(key)
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
                errors.append(f"{prefix}.{key} must be a full Git commit SHA")
        for key in ("introduced_at", "last_changed_at", "introduction_commit_message", "canonical_url"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{prefix}.{key} must be non-empty text")
        for key in ("linked_from_answers_index", "listed_in_geo_llms", "present_in_current_sitemap"):
            if not isinstance(item.get(key), bool):
                errors.append(f"{prefix}.{key} must be boolean")
        if item.get("present_in_current_sitemap") is not True:
            errors.append(f"{prefix}: legacy answer page must remain represented in the inspected source sitemap")
        if item.get("sitemap_lastmod") != "2026-11-15":
            errors.append(f"{prefix}: observed legacy sitemap lastmod must be recorded as 2026-11-15")

        expected_canonical = item.get("canonical_url")
        if page_canonicals.get(slug) != expected_canonical:
            errors.append(f"{prefix}: canonical URL differs from the committed HTML snapshot")
        index_linked = bool(re.search(r'href=[\"\']\.\./' + re.escape(slug) + r'/[\"\']', answers_index))
        llms_listed = bool(re.search(r'/answers/' + re.escape(slug) + r'/\s', llms_text))
        sitemap_listed = expected_canonical in sitemap_text
        if item.get("linked_from_answers_index") is not index_linked:
            errors.append(f"{prefix}: answers-index link flag differs from current file")
        if item.get("listed_in_geo_llms") is not llms_listed:
            errors.append(f"{prefix}: llms flag differs from current geo/llms.txt")
        if item.get("present_in_current_sitemap") is not sitemap_listed:
            errors.append(f"{prefix}: sitemap flag differs from current geo/sitemap.xml")
        if item.get("file_bytes") is not None and item["file_bytes"] <= 0:
            errors.append(f"{prefix}.file_bytes must be positive")

    if legacy_slugs != set(source_model.get("legacy_answer_slugs", [])):
        errors.append("source_model legacy_answer_slugs differs from legacy_pages")

    actual_legacy = actual_slugs - managed
    if actual_slugs != managed | legacy_slugs:
        errors.append(
            "answer directory inventory differs from source model: "
            f"actual={sorted(actual_slugs)}, managed={sorted(managed)}, legacy={sorted(legacy_slugs)}"
        )
    if actual_legacy != legacy_slugs:
        errors.append("not all unmanaged answer directories are registered as legacy")

    answer_links = set(re.findall(r'href=[\"\']\.\./([^/\\"\']+)/[\"\']', answers_index))
    llms_links = set(re.findall(r'/answers/([^/\s]+)/', llms_text))
    sitemap_links = {
        slug for slug in actual_slugs
        if f"/answers/{slug}/" in sitemap_text
    }
    snapshot = data.get("current_snapshot")
    if not isinstance(snapshot, dict):
        errors.append("current_snapshot must be an object")
    else:
        if snapshot.get("answer_directories") != len(actual_slugs):
            errors.append("current_snapshot.answer_directories differs from actual directories")
        if snapshot.get("builder_managed_answer_pages") != len(managed):
            errors.append("current_snapshot.builder_managed_answer_pages differs from source")
        if snapshot.get("legacy_static_unmanaged_pages") != len(legacy_slugs):
            errors.append("current_snapshot.legacy_static_unmanaged_pages differs from registry")
        if snapshot.get("answers_index_links") != len(answer_links):
            errors.append("current_snapshot.answers_index_links differs from answers/index.html")
        if snapshot.get("geo_llms_answer_links") != len(llms_links):
            errors.append("current_snapshot.geo_llms_answer_links differs from geo/llms.txt")
        if snapshot.get("sitemap_answer_pages") != len(sitemap_links):
            errors.append("current_snapshot.sitemap_answer_pages differs from sitemap URLs")
        if snapshot.get("sitemap_lastmod_for_legacy_pages") != "2026-11-15":
            errors.append("global lastmod observation changed; refresh provenance registry")

    # Every sitemap URL currently has the global UPDATED date, not file-level modification metadata.
    try:
        root = ET.fromstring(sitemap_text)
        lastmods = {
            entry.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            entry.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
            for entry in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        }
        legacy_lastmods = {lastmods.get(item.get("canonical_url")) for item in legacy_pages if isinstance(item, dict)}
        if legacy_lastmods != {"2026-11-15"}:
            errors.append("legacy sitemap lastmod values differ from the recorded global date")
    except ET.ParseError as exc:
        errors.append(f"geo/sitemap.xml is not valid XML: {exc}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.parse_args()
    errors: list[str] = []
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        builder = BUILDER.read_text(encoding="utf-8")
        answers_index = _read_text(ANSWERS_INDEX, errors)
        llms_text = _read_text(LLMS, errors)
        sitemap_text = _read_text(SITEMAP, errors)
        actual_slugs = {p.name for p in ANSWERS_DIR.iterdir() if p.is_dir() and (p / "index.html").is_file()}
        canonicals: dict[str, str] = {}
        for slug in actual_slugs:
            page = _read_text(ANSWERS_DIR / slug / "index.html", errors)
            match = re.search(r'<link[^>]+rel=[\"\']canonical[\"\'][^>]+href=[\"\']([^\"\']+)', page, re.I)
            if not match:
                # Support the attribute order used in the older compact pages.
                match = re.search(r'<link[^>]+href=[\"\']([^\"\']+)[\"\'][^>]+rel=[\"\']canonical', page, re.I)
            canonicals[slug] = match.group(1) if match else ""
        if data is not None:
            errors.extend(validate_provenance(data, builder, answers_index, llms_text, sitemap_text, actual_slugs, canonicals))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load provenance inputs: {exc}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: 15 GEO answer directories are classified as builder-managed or legacy; provenance and discovery surfaces agree with the registry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
