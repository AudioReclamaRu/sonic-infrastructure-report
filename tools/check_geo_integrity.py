#!/usr/bin/env python3
"""AI-Crawler Integrity Gate for the static GEO surface.

Local mode validates the checked-in artifact. --public compares every sitemap
page and machine-readable endpoint with the checked-in artifact for this exact
revision. It deliberately does not infer indexing from successful deployment.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
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
# Only machine resources genuinely served from this project path are listed.
MACHINE_FILES = ("llms.txt", "llms-full.txt", "sitemap.xml", "knowledge/studio-profile.json")


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
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n").strip()
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
            if "schema.org" not in str(obj.get("@context", "")):
                errors.append(f"{url}: JSON-LD object has no Schema.org @context")

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
        if not (geo_dir / filename).is_file():
            errors.append(f"missing machine-readable asset: geo/{filename}")

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


def audit_public(
    records: dict[str, PageRecord],
    urls: list[str],
    base_url: str,
    attempts: int = 3,
    timeout: float = 20.0,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    geo_dir = ROOT / "geo"

    def fetch_page(url: str) -> tuple[str, bytes]:
        status, body, final_url = _http_get(url, attempts, timeout)
        if status != 200:
            raise RuntimeError(f"HTTP {status}")
        final = urllib.parse.urlsplit(final_url)
        expected = urllib.parse.urlsplit(url)
        if final.scheme != expected.scheme or final.netloc != expected.netloc:
            raise RuntimeError(f"redirected to unexpected host: {final_url}")
        if final.path.rstrip("/") != expected.path.rstrip("/"):
            raise RuntimeError(f"redirected to unexpected path: {final_url}")
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
            status, body, _ = _http_get(url, attempts, timeout)
            if status != 200:
                errors.append(f"{url}: HTTP {status}")
                continue
            local_path = geo_dir / filename
            local_body = local_path.read_bytes()
            if normalized_hash(body) != normalized_hash(local_body):
                errors.append(f"{url}: public file differs from local artifact")
            if filename == "sitemap.xml":
                remote_urls = _read_sitemap_bytes(body)
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
        status, body, _ = _http_get(
            root_robots_url, attempts, timeout, allowed_status=(404,)
        )
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
                sample_url = base_url
                for agent in (
                    "Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot",
                    "ChatGPT-User", "ClaudeBot", "PerplexityBot",
                ):
                    if not robot_parser.can_fetch(agent, sample_url):
                        notes.append(
                            f"HOST ROBOTS: {agent} is disallowed from {sample_url}"
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
