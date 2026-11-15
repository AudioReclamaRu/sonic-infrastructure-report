#!/usr/bin/env python3
"""AI-Crawler Integrity Gate for the static GEO surface.

Local mode validates the checked-in artifact. --public compares every sitemap
page and machine-readable endpoint with the checked-in artifact for this exact
revision. It deliberately does not infer indexing from successful deployment.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "geo"
DEFAULT_BASE_URL = (
    "https://audioreclamaru.github.io/sonic-infrastructure-report/geo/"
)
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
BUILD_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)
# A robots.txt inside /geo/ is not the host's authoritative /robots.txt.
# These machine-readable assets are served from this project path and are
# compared byte-for-byte in public mode. The host-root robots policy is checked
# separately below.
MACHINE_FILES = (
    "llms.txt",
    "llms-full.txt",
    "sitemap.xml",
    "pricing.json",
    "faq.json",
    "feed.json",
    "knowledge/combined.json",
    "knowledge/blog-facts.json",
    "knowledge/evidence-ledger.json",
    "knowledge/case-studies.json",
    "knowledge/query-matrix.json",
    "knowledge/evidence-ledger.csv",
    "knowledge/query-matrix.csv",
    "rss.xml",
    "opensearch.xml",
    "a7f3c9d2e4b6481fa0c5d7e9b2f4a6c8.txt",
)
MACHINE_JSON_FILES = frozenset({
    "pricing.json",
    "faq.json",
    "feed.json",
    "knowledge/combined.json",
    "knowledge/blog-facts.json",
    "knowledge/evidence-ledger.json",
    "knowledge/case-studies.json",
    "knowledge/query-matrix.json",
})
MACHINE_XML_FILES = frozenset({"sitemap.xml", "rss.xml", "opensearch.xml"})
MACHINE_CSV_FILES = frozenset({
    "knowledge/evidence-ledger.csv",
    "knowledge/query-matrix.csv",
})
# Search/index discovery tokens. A denial for any sitemap URL or machine
# endpoint is a public-verification failure.
# Vendor references:
# - OpenAI: https://developers.openai.com/api/docs/bots
# - Anthropic: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
# - Perplexity: https://docs.perplexity.ai/docs/resources/perplexity-crawlers
# - Google: https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
INDEXING_CRAWLERS = (
    "Googlebot", "Bingbot", "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot",
)
# These product tokens do not themselves decide search-index inclusion. They
# govern training, grounding, or user-triggered retrieval and are reported as
# policy notes rather than indexing failures. Google-Extended is a robots token,
# not a distinct HTTP request user-agent; ChatGPT-User and Perplexity-User may
# not honor robots.txt for user-requested fetches.
ADDITIONAL_CRAWLERS = (
    "Google-Extended", "GPTBot", "ChatGPT-User",
    "ClaudeBot", "Claude-User", "Perplexity-User",
)


class PageParser(HTMLParser):
    """Extract crawl-critical HTML metadata and parse every JSON-LD block."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, list[str]] = {}
        self.canonicals: list[str] = []
        self.jsonld: list[Any] = []
        self.jsonld_errors: list[str] = []
        self.title_parts: list[str] = []
        self._in_title = False
        self._script_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        tag = tag.lower()
        if tag == "meta" and values.get("name"):
            self.meta.setdefault(values["name"].lower(), []).append(
                values.get("content", "").strip()
            )
        elif tag == "link" and "canonical" in values.get("rel", "").lower().split():
            self.canonicals.append(values.get("href", "").strip())
        elif tag == "title":
            self._in_title = True
        elif (
            tag == "script"
            and values.get("type", "").lower() == "application/ld+json"
        ):
            if self._script_parts is not None:
                self.jsonld_errors.append("nested JSON-LD script element")
            else:
                self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._script_parts is not None:
            self._script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._script_parts is not None:
            raw = "".join(self._script_parts).strip()
            self._script_parts = None
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    self.jsonld.extend(parsed)
                else:
                    self.jsonld.append(parsed)
            except (json.JSONDecodeError, TypeError) as exc:
                self.jsonld_errors.append(f"invalid JSON-LD: {exc}")


@dataclass
class PageRecord:
    url: str
    path: Path
    build_sha: str
    canonical: str
    jsonld: list[Any]
    content_hash: str


def normalized_hash(data: bytes) -> str:
    """Hash the exact static body, allowing only CRLF/LF normalization."""
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def parse_page(path: Path, url: str) -> tuple[PageParser, bytes]:
    body = path.read_bytes()
    parser = PageParser()
    parser.feed(body.decode("utf-8"))
    parser.close()
    return parser, body


def local_path_for_url(url: str, base_url: str, geo_dir: Path) -> Path:
    target = urllib.parse.urlsplit(url)
    base = urllib.parse.urlsplit(base_url)
    base_path = base.path if base.path.endswith("/") else base.path + "/"
    if target.scheme != base.scheme or target.netloc != base.netloc:
        raise ValueError(f"URL is outside GEO base: {url}")
    if not target.path.startswith(base_path) or target.query or target.fragment:
        raise ValueError(f"URL is outside GEO path or contains query/fragment: {url}")
    relative = urllib.parse.unquote(target.path[len(base_path):])
    if not relative:
        relative = "index.html"
    elif relative.endswith("/"):
        relative += "index.html"
    candidate = (geo_dir / relative).resolve()
    root = geo_dir.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"URL escapes GEO directory: {url}")
    return candidate


def has_schema_org_context(context: Any) -> bool:
    """Accept canonical Schema.org JSON-LD contexts, not substring lookalikes."""
    if isinstance(context, str):
        return context.rstrip("/") in {"https://schema.org", "http://schema.org"}
    if isinstance(context, list):
        return any(has_schema_org_context(item) for item in context)
    if isinstance(context, dict):
        return has_schema_org_context(context.get("@vocab"))
    return False


def jsonld_types(objects: list[Any]) -> list[str]:
    found: list[str] = []
    for obj in objects:
        if not isinstance(obj, dict):
            found.append("<non-object>")
            continue
        value = obj.get("@type")
        if isinstance(value, list):
            found.extend(str(item) for item in value)
        elif value:
            found.append(str(value))
        else:
            found.append("<missing @type>")
    return found


def _read_sitemap(path: Path) -> list[str]:
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != SITEMAP_NS + "urlset":
        raise ValueError(f"unexpected sitemap root: {root.tag}")
    urls: list[str] = []
    for entry in root.findall(SITEMAP_NS + "url"):
        loc = entry.find(SITEMAP_NS + "loc")
        if loc is None or not (loc.text or "").strip():
            raise ValueError("sitemap contains <url> without <loc>")
        urls.append((loc.text or "").strip())
    return urls



def query_matrix_view_errors(
    query_rows: Any,
    html_content: str,
    csv_headers: list[str],
    csv_rows: list[dict[str, str | None]],
    known_ids: set[str],
) -> list[str]:
    """Keep query-matrix HTML/CSV views and evidence links aligned with JSON."""
    errors: list[str] = []
    if not isinstance(query_rows, list):
        return ["query-matrix.json rows must be an array"]

    clusters: set[str] = set()
    expected_headers: list[str] = []
    for row_number, row in enumerate(query_rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"query-matrix.json row {row_number} is not an object")
            continue
        for field_name in row:
            if field_name not in expected_headers:
                expected_headers.append(field_name)

        cluster = str(row.get("cluster") or "").strip()
        if not cluster:
            errors.append(f"query-matrix.json row {row_number} has no cluster")
        elif cluster in clusters:
            errors.append(f"query-matrix.json contains duplicate cluster: {cluster}")
        else:
            clusters.add(cluster)
            if cluster not in html_content:
                errors.append(f"query-matrix.html is missing cluster: {cluster}")

        # JSON is the source of truth: detect stale visible content, not just
        # missing clusters. Every public row field must survive into its HTML view.
        for field_name in (
            "intent", "example_queries", "supporting_facts", "gap", "status",
            "target_main_url",
        ):
            expected_value = str(row.get(field_name) or "").strip()
            if expected_value and html.escape(expected_value, quote=False) not in html_content:
                errors.append(
                    f"query-matrix.html is missing or has stale {field_name} "
                    f"for cluster: {cluster or row_number}"
                )

        target_geo = str(row.get("target_geo_url") or "").strip()
        if target_geo:
            for target in re.split(r"\\s*;\\s*", target_geo):
                if target and html.escape(target, quote=True) not in html_content:
                    errors.append(
                        f"query-matrix.html is missing target GEO URL for "
                        f"cluster {cluster!r}: {target}"
                    )

        references = row.get("supporting_fact_ids")
        if not isinstance(references, list):
            errors.append(
                f"query-matrix row {cluster or row_number!r} "
                "must contain supporting_fact_ids as an array"
            )
            continue
        seen_references: set[str] = set()
        for reference in references:
            if not isinstance(reference, str) or not reference.strip():
                errors.append(
                    f"query-matrix row {cluster or row_number!r} "
                    "contains an empty or non-string supporting_fact_id"
                )
                continue
            if reference in seen_references:
                errors.append(
                    f"query-matrix row {cluster!r} contains duplicate ID: {reference}"
                )
            seen_references.add(reference)
            if reference not in known_ids:
                errors.append(
                    f"query-matrix row {cluster!r} references unknown ID: {reference}"
                )

    if csv_headers != expected_headers:
        errors.append(
            "query-matrix.csv header does not match query-matrix.json fields"
        )
    if len(csv_rows) != len(query_rows):
        errors.append(
            "query-matrix.csv row count differs from query-matrix.json "
            f"({len(csv_rows)} != {len(query_rows)})"
        )
    for row_number, (expected, actual) in enumerate(
        zip(query_rows, csv_rows), start=1
    ):
        if not isinstance(expected, dict):
            continue
        for field_name in expected:
            value = expected[field_name]
            expected_text = (
                json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                if isinstance(value, (list, dict))
                else "" if value is None else str(value)
            )
            if actual.get(field_name) != expected_text:
                errors.append(
                    f"query-matrix.csv row {row_number} field {field_name} "
                    "differs from query-matrix.json"
                )
                break
    return errors

def audit_local(
    root: Path = ROOT, base_url: str = DEFAULT_BASE_URL
) -> tuple[list[str], dict[str, PageRecord], list[str]]:
    errors: list[str] = []
    geo_dir = root / "geo"
    sitemap_path = geo_dir / "sitemap.xml"
    if not sitemap_path.is_file():
        return [f"missing {sitemap_path}"], {}, []

    try:
        urls = _read_sitemap(sitemap_path)
    except (ET.ParseError, OSError, ValueError) as exc:
        return [f"cannot parse sitemap: {exc}"], {}, []

    if not urls:
        errors.append("sitemap contains zero URLs")
    if len(urls) != len(set(urls)):
        errors.append("sitemap contains duplicate <loc> URLs")

    records: dict[str, PageRecord] = {}
    listed_paths: set[Path] = set()
    build_shas: dict[str, list[str]] = {}

    for url in urls:
        try:
            page_path = local_path_for_url(url, base_url, geo_dir)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if page_path in listed_paths:
            errors.append(f"{url}: multiple sitemap URLs map to {page_path}")
        listed_paths.add(page_path)

        if not page_path.is_file():
            errors.append(f"{url}: sitemap target does not exist: {page_path}")
            continue

        try:
            parser, body = parse_page(page_path, url)
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{url}: cannot read HTML: {exc}")
            continue

        prefix = url.rstrip("/")
        if not parser.title_parts or not "".join(parser.title_parts).strip():
            errors.append(f"{url}: missing <title>")
        if len(parser.canonicals) != 1:
            errors.append(
                f"{url}: expected exactly one canonical link, found {len(parser.canonicals)}"
            )
        elif parser.canonicals[0] != url:
            errors.append(
                f"{url}: canonical mismatch: {parser.canonicals[0]!r}"
            )

        robots = parser.meta.get("robots", [])
        if len(robots) != 1:
            errors.append(
                f"{url}: expected exactly one robots meta, found {len(robots)}"
            )
        elif "noindex" in robots[0].lower() or robots[0].strip().lower() == "none":
            errors.append(f"{url}: page is marked noindex")

        shas = parser.meta.get("build-sha", [])
        if len(shas) != 1:
            errors.append(
                f"{url}: expected exactly one build-sha meta, found {len(shas)}"
            )
            build_sha = ""
        else:
            build_sha = shas[0]
            if not BUILD_SHA_RE.fullmatch(build_sha):
                errors.append(f"{url}: invalid build-sha value: {build_sha!r}")
            else:
                build_shas.setdefault(build_sha.lower(), []).append(url)

        if parser.jsonld_errors:
            for issue in parser.jsonld_errors:
                errors.append(f"{url}: {issue}")
        if not parser.jsonld:
            errors.append(f"{url}: no JSON-LD structured data")
        for obj in parser.jsonld:
            if not isinstance(obj, dict):
                errors.append(f"{url}: JSON-LD top-level value is not an object")
                continue
            if not has_schema_org_context(obj.get("@context")):
                errors.append(f"{url}: JSON-LD object has no canonical Schema.org @context")

        types = jsonld_types(parser.jsonld)
        counts: dict[str, int] = {}
        for item in types:
            counts[item] = counts.get(item, 0) + 1
        for item, count in counts.items():
            if item.startswith("<"):
                errors.append(f"{url}: JSON-LD object {item}")
            elif count > 1:
                errors.append(f"{url}: duplicate top-level JSON-LD type {item} ({count})")

        is_geo_root = url.rstrip("/") == base_url.rstrip("/")
        breadcrumb_count = types.count("BreadcrumbList")
        if not is_geo_root and breadcrumb_count != 1:
            errors.append(
                f"{url}: expected exactly one BreadcrumbList, found {breadcrumb_count}"
            )

        creative_work_types = {
            "FAQPage", "WebPage", "CollectionPage", "Dataset", "Article", "BlogPosting",
            "NewsArticle", "CreativeWork", "TechArticle", "HowTo",
        }
        for obj in parser.jsonld:
            if isinstance(obj, dict) and "dateModified" in obj:
                obj_types = obj.get("@type", [])
                if isinstance(obj_types, str):
                    obj_types = [obj_types]
                if not any(item in creative_work_types for item in obj_types):
                    errors.append(
                        f"{url}: dateModified is attached to non-CreativeWork "
                        f"type {obj_types!r}"
                    )

        records[url] = PageRecord(
            url=url,
            path=page_path,
            build_sha=build_sha,
            canonical=parser.canonicals[0] if len(parser.canonicals) == 1 else "",
            jsonld=parser.jsonld,
            content_hash=normalized_hash(body),
        )

    actual_html = {p.resolve() for p in geo_dir.rglob("*.html")}
    missing_from_sitemap = sorted(str(p.relative_to(root)) for p in actual_html - listed_paths)
    if missing_from_sitemap:
        errors.append(
            "HTML pages missing from sitemap: " + ", ".join(missing_from_sitemap)
        )
    sitemap_without_html = sorted(str(p) for p in listed_paths - actual_html)
    if sitemap_without_html:
        errors.append(
            "sitemap targets not represented by local HTML: " + ", ".join(sitemap_without_html)
        )

    for filename in MACHINE_FILES:
        asset_path = geo_dir / filename
        if not asset_path.is_file():
            errors.append(f"missing machine-readable asset: geo/{filename}")
            continue
        try:
            body = asset_path.read_bytes()
            if not body.strip():
                raise ValueError("asset is empty")
            decoded = body.decode("utf-8")
            if filename in MACHINE_JSON_FILES:
                parsed = json.loads(decoded)
                if not isinstance(parsed, (dict, list)):
                    raise ValueError("JSON top-level value must be an object or array")
            elif filename in MACHINE_XML_FILES:
                ET.fromstring(body)
            elif filename in MACHINE_CSV_FILES:
                rows = csv.reader(decoded.splitlines())
                headers = next(rows, None)
                if not headers or any(not item.strip() for item in headers):
                    raise ValueError("CSV has no valid header row")
                for row_number, row in enumerate(rows, start=2):
                    if len(row) != len(headers):
                        raise ValueError(
                            f"CSV row {row_number} has {len(row)} fields; "
                            f"expected {len(headers)}"
                        )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError,
                ET.ParseError, csv.Error, ValueError, StopIteration) as exc:
            errors.append(
                f"invalid machine-readable asset geo/{filename}: {exc}"
            )

    # Keep the public machine representations synchronized with their canonical
    # evidence objects. Syntax-only checks cannot catch stale but valid JSON/CSV.
    blog_path = geo_dir / "knowledge" / "blog-facts.json"
    ledger_path = geo_dir / "knowledge" / "evidence-ledger.json"
    cases_path = geo_dir / "knowledge" / "case-studies.json"
    queries_path = geo_dir / "knowledge" / "query-matrix.json"
    combined_path = geo_dir / "knowledge" / "combined.json"
    csv_path = geo_dir / "knowledge" / "evidence-ledger.csv"
    try:
        blog_data = json.loads(blog_path.read_text(encoding="utf-8"))
        ledger_data = json.loads(ledger_path.read_text(encoding="utf-8"))
        cases_data = json.loads(cases_path.read_text(encoding="utf-8"))
        queries_data = json.loads(queries_path.read_text(encoding="utf-8"))
        pricing_data = json.loads((geo_dir / "pricing.json").read_text(encoding="utf-8"))
        combined_data = json.loads(combined_path.read_text(encoding="utf-8"))
        blog_facts = blog_data.get("facts", [])
        ledger_rows = ledger_data.get("rows", [])
        if not isinstance(blog_facts, list) or not isinstance(ledger_rows, list):
            raise ValueError("blog facts and evidence ledger must contain arrays")
        if combined_data.get("blog_facts") != blog_data:
            errors.append(
                "geo/knowledge/combined.json blog_facts differs from blog-facts.json"
            )
        if combined_data.get("evidence_ledger") != ledger_data:
            errors.append(
                "geo/knowledge/combined.json evidence_ledger differs from evidence-ledger.json"
            )
        if combined_data.get("case_studies") != cases_data:
            errors.append(
                "geo/knowledge/combined.json case_studies differs from case-studies.json"
            )
        if combined_data.get("query_matrix") != queries_data:
            errors.append(
                "geo/knowledge/combined.json query_matrix differs from query-matrix.json"
            )

        ledger_by_id: dict[str, dict[str, Any]] = {}
        for row in ledger_rows:
            if not isinstance(row, dict) or not row.get("id"):
                errors.append("evidence-ledger.json contains a row without an id")
                continue
            row_id = str(row["id"])
            if row_id in ledger_by_id:
                errors.append(f"evidence-ledger.json contains duplicate id: {row_id}")
            ledger_by_id[row_id] = row

        blog_ids: set[str] = set()
        for fact in blog_facts:
            if not isinstance(fact, dict) or not fact.get("id"):
                errors.append("blog-facts.json contains a fact without an id")
                continue
            fact_id = str(fact["id"])
            if fact_id in blog_ids:
                errors.append(f"blog-facts.json contains duplicate id: {fact_id}")
            blog_ids.add(fact_id)
            evidence = ledger_by_id.get(fact_id)
            if evidence is None:
                errors.append(
                    f"blog-facts.json fact {fact_id} has no evidence-ledger row"
                )
                continue
            if fact.get("verification_status") != evidence.get("status"):
                errors.append(
                    f"{fact_id}: blog verification_status differs from evidence-ledger status"
                )
            if fact.get("phase3_classification") != evidence.get("phase3_classification"):
                errors.append(
                    f"{fact_id}: blog phase3_classification differs from evidence ledger"
                )

        price_entries = pricing_data.get("entries", [])
        case_rows = cases_data.get("cases", [])
        if not isinstance(price_entries, list) or not isinstance(case_rows, list):
            raise ValueError("pricing entries and case studies must contain arrays")
        known_ids = set(ledger_by_id)
        known_ids.update(
            str(row["id"]) for row in price_entries
            if isinstance(row, dict) and row.get("id")
        )
        known_ids.update(
            str(row["id"]) for row in case_rows
            if isinstance(row, dict) and row.get("id")
        )

        query_html_path = geo_dir / "knowledge" / "query-matrix" / "index.html"
        if not query_html_path.is_file():
            errors.append("missing query-matrix HTML view: geo/knowledge/query-matrix/index.html")
            query_html = ""
        else:
            query_html = query_html_path.read_text(encoding="utf-8")
        query_csv_path = geo_dir / "knowledge" / "query-matrix.csv"
        with query_csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            query_reader = csv.DictReader(stream)
            query_csv_rows = list(query_reader)
            query_csv_headers = query_reader.fieldnames or []
        errors.extend(query_matrix_view_errors(
            queries_data.get("rows", []),
            query_html,
            query_csv_headers,
            query_csv_rows,
            known_ids,
        ))

        with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            csv_rows = list(reader)
            csv_headers = reader.fieldnames or []
        if not ledger_rows:
            errors.append("evidence-ledger.json contains no rows")
        else:
            expected_headers: list[str] = []
            for ledger_row in ledger_rows:
                for field_name in ledger_row:
                    if field_name not in expected_headers:
                        expected_headers.append(field_name)
            if csv_headers != expected_headers:
                errors.append(
                    "evidence-ledger.csv header does not match the union of "
                    "evidence-ledger.json fields"
                )
            csv_by_id: dict[str, dict[str, str | None]] = {}
            for row in csv_rows:
                row_id = str(row.get("id") or "")
                if not row_id:
                    errors.append("evidence-ledger.csv contains a row without an id")
                    continue
                if row_id in csv_by_id:
                    errors.append(f"evidence-ledger.csv contains duplicate id: {row_id}")
                csv_by_id[row_id] = row
            if set(csv_by_id) != set(ledger_by_id):
                errors.append(
                    "evidence-ledger.csv ids differ from evidence-ledger.json "
                    f"(missing={sorted(set(ledger_by_id) - set(csv_by_id))}, "
                    f"extra={sorted(set(csv_by_id) - set(ledger_by_id))})"
                )
            for row_id, expected in ledger_by_id.items():
                actual = csv_by_id.get(row_id)
                if actual is None:
                    continue
                for key, value in expected.items():
                    expected_text = "" if value is None else str(value)
                    if actual.get(key) != expected_text:
                        errors.append(
                            f"evidence-ledger.csv row {row_id} field {key} "
                            "differs from evidence-ledger.json"
                        )
                        break
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, csv.Error,
            AttributeError, TypeError, ValueError) as exc:
        errors.append(f"cannot validate GEO knowledge crosswalks: {exc}")

    if len(build_shas) > 1:
        summary = ", ".join(
            f"{sha}: {len(page_urls)} pages" for sha, page_urls in sorted(build_shas.items())
        )
        # Different source revisions can legitimately coexist for hand-maintained
        # legacy pages; report them as a warning in the summary, not as failure.
        print(f"NOTE: per-page build-sha revisions: {summary}")

    return errors, records, urls


def _http_get(
    url: str, attempts: int, timeout: float,
    allowed_status: tuple[int, ...] = (),
) -> tuple[int, bytes, str]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "AudioReclama-GEO-Integrity/1.0",
                "Cache-Control": "no-cache, no-store, max-age=0",
                "Pragma": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, response.read(), response.geturl()
        except urllib.error.HTTPError as exc:
            if exc.code in allowed_status:
                return exc.code, exc.read(), exc.geturl()
            last_error = exc
            if exc.code < 500 and exc.code != 429:
                break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
        if attempt + 1 < attempts:
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"GET failed after {attempts} attempt(s): {last_error}")


def _validate_final_url(requested_url: str, final_url: str) -> None:
    """Reject cross-origin or cross-path redirects for every public probe."""
    requested = urllib.parse.urlsplit(requested_url)
    final = urllib.parse.urlsplit(final_url)
    if final.scheme != requested.scheme or final.netloc != requested.netloc:
        raise RuntimeError(f"redirected to unexpected origin: {final_url}")
    if final.path.rstrip("/") != requested.path.rstrip("/"):
        raise RuntimeError(f"redirected to unexpected path: {final_url}")


def audit_public(
    records: dict[str, PageRecord],
    urls: list[str],
    base_url: str,
    attempts: int = 3,
    timeout: float = 20.0,
    root: Path = ROOT,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    geo_dir = root / "geo"

    def fetch_page(url: str) -> tuple[str, bytes]:
        status, body, final_url = _http_get(url, attempts, timeout)
        if status != 200:
            raise RuntimeError(f"HTTP {status}")
        _validate_final_url(url, final_url)
        return url, body

    verify_token = str(int(time.time()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {}
        for url in urls:
            separator = "&" if "?" in url else "?"
            probe_url = f"{url}{separator}__geo_verify={verify_token}"
            futures[pool.submit(fetch_page, probe_url)] = url

        for future, original_url in list(futures.items()):
            local = records.get(original_url)
            try:
                _, body = future.result()
            except Exception as exc:
                errors.append(f"{original_url}: public fetch failed: {exc}")
                continue
            if local is None:
                errors.append(f"{original_url}: no local reference record")
                continue

            remote_hash = normalized_hash(body)
            if remote_hash != local.content_hash:
                errors.append(
                    f"{original_url}: public HTML differs from local artifact "
                    f"(local sha256 {local.content_hash[:12]}, "
                    f"public {remote_hash[:12]})"
                )

            try:
                parser = PageParser()
                parser.feed(body.decode("utf-8"))
                parser.close()
            except UnicodeDecodeError as exc:
                errors.append(f"{original_url}: public HTML is not UTF-8: {exc}")
                continue

            remote_sha = parser.meta.get("build-sha", [])
            if remote_sha != [local.build_sha]:
                errors.append(
                    f"{original_url}: public build-sha {remote_sha!r} "
                    f"does not match local {[local.build_sha]!r}"
                )
            if parser.canonicals != [local.canonical]:
                errors.append(
                    f"{original_url}: public canonical {parser.canonicals!r} "
                    f"does not match local {[local.canonical]!r}"
                )
            if parser.jsonld_errors or parser.jsonld != local.jsonld:
                errors.append(
                    f"{original_url}: public JSON-LD differs from local artifact"
                )

    # Confirm project-path machine-readable entry points. A /geo/robots.txt
    # file is not authoritative: robots.txt is scoped to the host root.
    for filename in MACHINE_FILES:
        url = base_url + filename
        try:
            status, body, final_url = _http_get(url, attempts, timeout)
            _validate_final_url(url, final_url)
            if status != 200:
                errors.append(f"{url}: HTTP {status}")
                continue
            local_path = geo_dir / filename
            local_body = local_path.read_bytes()
            if normalized_hash(body) != normalized_hash(local_body):
                errors.append(f"{url}: public file differs from local artifact")
            if filename == "sitemap.xml":
                remote_urls = _read_sitemap_bytes(body)
                if len(remote_urls) != len(set(remote_urls)):
                    errors.append(f"{url}: public sitemap contains duplicate <loc> URLs")
                if set(remote_urls) != set(urls):
                    errors.append(f"{url}: public sitemap URL set differs from local")
        except Exception as exc:
            errors.append(f"{url}: public fetch failed: {exc}")

    # robots.txt has host-root scope, not project-subdirectory scope. Check
    # the true host endpoint separately; a 404 means no host policy is
    # published, not that /geo/robots.txt becomes authoritative.
    parsed_base = urllib.parse.urlsplit(base_url)
    root_robots_url = f"{parsed_base.scheme}://{parsed_base.netloc}/robots.txt"
    try:
        status, body, final_url = _http_get(
            root_robots_url, attempts, timeout, allowed_status=(404,)
        )
        _validate_final_url(root_robots_url, final_url)
        if status == 404:
            notes.append(
                f"HOST ROBOTS: {root_robots_url} returns 404. "
                "No host-level robots policy or Sitemap directive is published; "
                "the /geo/robots.txt copy is not authoritative. "
                "A missing robots.txt does not itself disallow crawling."
            )
        elif status == 200:
            robots_text = body.decode("utf-8", errors="replace")
            sitemap_url = base_url + "sitemap.xml"
            if sitemap_url not in robots_text:
                notes.append(
                    f"HOST ROBOTS: root robots.txt does not advertise {sitemap_url}"
                )
            try:
                from urllib.robotparser import RobotFileParser

                robot_parser = RobotFileParser()
                robot_parser.parse(robots_text.splitlines())
                crawl_targets = list(dict.fromkeys(
                    urls + [base_url + filename for filename in MACHINE_FILES]
                ))
                for agent in INDEXING_CRAWLERS:
                    for target in crawl_targets:
                        if not robot_parser.can_fetch(agent, target):
                            errors.append(
                                f"HOST ROBOTS: {agent} is disallowed from {target}"
                            )
                for agent in ADDITIONAL_CRAWLERS:
                    for target in crawl_targets:
                        if not robot_parser.can_fetch(agent, target):
                            notes.append(
                                f"HOST ROBOTS: {agent} is disallowed from {target} "
                                "(separate training/grounding/user-fetch policy)"
                            )
            except Exception as exc:
                notes.append(f"HOST ROBOTS: could not interpret crawler rules: {exc}")
        else:
            errors.append(f"{root_robots_url}: unexpected HTTP {status}")
    except Exception as exc:
        errors.append(f"{root_robots_url}: fetch failed: {exc}")

    return errors, notes


def _read_sitemap_bytes(body: bytes) -> list[str]:
    root = ET.fromstring(body)
    if root.tag != SITEMAP_NS + "urlset":
        raise ValueError(f"unexpected sitemap root: {root.tag}")
    locs: list[str] = []
    for entry in root.findall(SITEMAP_NS + "url"):
        loc = entry.find(SITEMAP_NS + "loc")
        if loc is None or not (loc.text or "").strip():
            raise ValueError("public sitemap contains <url> without <loc>")
        locs.append((loc.text or "").strip())
    return locs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public",
        action="store_true",
        help="compare deployed pages and crawler endpoints with local files",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"GEO public base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/") + "/"
    errors, records, urls = audit_local(ROOT, base_url)
    if errors:
        print("AI-CRAWLER INTEGRITY GATE: FAIL (local)")
        for issue in errors:
            print(f" - {issue}")
        return 1

    print(
        f"AI-CRAWLER INTEGRITY GATE: PASS (local) — "
        f"{len(records)} sitemap pages, {len(MACHINE_FILES)} machine endpoints"
    )
    if not args.public:
        return 0

    public_errors, public_notes = audit_public(
        records, urls, base_url, attempts=max(1, args.attempts),
        timeout=max(1.0, args.timeout),
    )
    for note in public_notes:
        print(f"NOTE: {note}")
    if public_errors:
        print("GEO PUBLIC DEPLOY VERIFICATION: FAIL")
        for issue in public_errors:
            print(f" - {issue}")
        return 1

    print(
        f"GEO PUBLIC DEPLOY VERIFICATION: PASS — "
        f"{len(records)} HTML pages and {len(MACHINE_FILES)} machine endpoints "
        "match the checked-out deployment artifact"
    )
    print("Indexing status: NOT CHECKED (deployment is not proof of indexing).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
