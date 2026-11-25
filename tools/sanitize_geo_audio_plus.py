#!/usr/bin/env python3
"""Fact-safe publication sanitizer for the static GEO/AEO Pages surface.

The official website and the Audio+ product domain are read-only. This tool
only sanitizes repository-generated geo/**/*.html before the existing Pages
workflow uploads its artifact. It never fetches or writes to either website.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GEO_ROOT = ROOT / "geo"

JSON_LD_RE = re.compile(
    r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.IGNORECASE | re.DOTALL,
)
AUDIO_PLUS_MARKER_RE = re.compile(r"audio\s*\+|аудио\s*\+|audioplus|аудиоплюс|audio\.plus|/audioplus", re.IGNORECASE)
PRICE_RE = re.compile(
    r"(?<!\d)(?:49\s?990|35\s?990|18\s?990|1\s?990|1990|790)\s*(?:₽|RUB)",
    re.IGNORECASE,
)
WORDS_RE = re.compile(r"до\s*90\s*слов(?!\s*\(наблюдение индексированного снимка)", re.IGNORECASE)

PRICE_OBSERVATION = (
    "сумма из индексированного снимка (не текущая цена; live-проверка не выполнена)"
)
EDIT_OBSERVATION = (
    "опция изменений из индексированного снимка (не подтверждена как действующее условие)"
)
WORDS_OBSERVATION = (
    "до 90 слов (наблюдение индексированного снимка; live-проверка не выполнена)"
)
SAFE_ANSWER = (
    "Текущая цена и применимость изменений Audio+ не подтверждены live. "
    "В индексированном снимке страницы от 25.11.2026 наблюдались значения интерфейса, "
    "но они не являются текущим прайсом или безусловным обещанием услуги. "
    "Интерфейс и датированная оферта расходятся по изменениям и категории "
    "video voice-over; проверьте текущую страницу продукта и действующую оферту."
)
NOTICE = (
    '<aside class="audio-plus-source-status" role="note" '
    'style="margin:1em 0;padding:12px 16px;border-left:4px solid #a66;background:#fafafa">'
    '<strong>Актуальность условий Audio+.</strong> Текущие цены и опции изменений '
    'не подтверждены live. Индексированные суммы — датированные наблюдения, '
    'а не текущий прайс. В интерфейсе и датированной оферте есть неразрешённые '
    'различия по изменениям и video voice-over. '
    '<a href="https://audio.plus/">Страница продукта</a> · '
    '<a href="https://audio.plus/offer.html">Публичная оферта</a>.'
    '</aside>'
)


def _audio_plus_offer(node: Any) -> bool:
    if isinstance(node, dict):
        if node.get("@type") == "Offer":
            haystack = json.dumps(node, ensure_ascii=False).lower()
            return (
                "audio+" in haystack
                or "аудио+" in haystack
                or "audioplus" in haystack
                or "audio.plus" in haystack
            )
        return any(_audio_plus_offer(value) for value in node.values())
    if isinstance(node, list):
        return any(_audio_plus_offer(value) for value in node)
    return False


def _sanitize_json(value: Any, question_context: str = "") -> tuple[Any, int]:
    changes = 0
    if isinstance(value, list):
        out = []
        for item in value:
            if _audio_plus_offer(item):
                changes += 1
                continue
            clean, count = _sanitize_json(item, question_context)
            out.append(clean)
            changes += count
        return out, changes
    if isinstance(value, dict):
        local_context = question_context
        q = value.get("name")
        if isinstance(q, str) and AUDIO_PLUS_MARKER_RE.search(q):
            local_context = q
        out = {}
        for key, item in value.items():
            if key == "offers" and _audio_plus_offer(item):
                changes += 1
                continue
            if key == "text" and isinstance(item, str) and AUDIO_PLUS_MARKER_RE.search(local_context):
                if re.search(r"\d.*(?:₽|RUB)|правк|измен|90 слов|один заказ", item, re.IGNORECASE):
                    out[key] = SAFE_ANSWER
                    changes += 1
                    continue
            clean, count = _sanitize_json(item, local_context)
            out[key] = clean
            changes += count
        return out, changes
    return value, changes


def sanitize_html(html: str) -> tuple[str, int]:
    if not AUDIO_PLUS_MARKER_RE.search(html):
        return html, 0

    changes = 0

    def replace_json_ld(match: re.Match[str]) -> str:
        nonlocal changes
        opening, payload, closing = match.groups()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            # Leave malformed JSON-LD untouched; the publication check will flag it.
            return match.group(0)
        clean, count = _sanitize_json(data)
        changes += count
        return opening + json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + closing

    html = JSON_LD_RE.sub(replace_json_ld, html)

    def price_replacement(match: re.Match[str]) -> str:
        nonlocal changes
        changes += 1
        token = match.group(0)
        if "790" in token:
            return EDIT_OBSERVATION
        return PRICE_OBSERVATION

    html = PRICE_RE.sub(price_replacement, html)
    html, words_count = WORDS_RE.subn(WORDS_OBSERVATION, html)
    changes += words_count

    # Old internal references to the product route should resolve to the actual product domain.
    html, link_count = re.subn(
        r"https?://www\.audio-reclama\.ru/audioplus/?",
        "https://audio.plus/",
        html,
        flags=re.IGNORECASE,
    )
    changes += link_count

    if "audio-plus-source-status" not in html:
        h1_end = re.search(r"</h1\s*>", html, re.IGNORECASE)
        if h1_end:
            html = html[:h1_end.end()] + NOTICE + html[h1_end.end():]
        else:
            body_start = re.search(r"<body\b[^>]*>", html, re.IGNORECASE)
            if body_start:
                html = html[:body_start.end()] + NOTICE + html[body_start.end():]
        changes += 1

    return html, changes


def inspect_html(html: str) -> list[str]:
    errors = []
    for match in JSON_LD_RE.finditer(html):
        try:
            data = json.loads(match.group(2))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON-LD: {exc}")
            continue
        if _audio_plus_offer(data):
            errors.append("Audio+ Offer remains in JSON-LD")
        serialized = json.dumps(data, ensure_ascii=False)
        if AUDIO_PLUS_MARKER_RE.search(serialized) and PRICE_RE.search(serialized):
            errors.append("unverified Audio+ numeric price remains in JSON-LD")
    if AUDIO_PLUS_MARKER_RE.search(html) and PRICE_RE.search(html):
        errors.append("unverified Audio+ numeric price remains in HTML")
    if AUDIO_PLUS_MARKER_RE.search(html) and "audio-plus-source-status" not in html:
        errors.append("Audio+ page has no source-status notice")
    return errors


def run(*, apply: bool) -> int:
    if not GEO_ROOT.exists():
        print(f"GEO directory not found: {GEO_ROOT}")
        return 2
    changed = []
    errors = []
    scanned = 0
    for path in sorted(GEO_ROOT.rglob("*.html")):
        original = path.read_text(encoding="utf-8")
        sanitized, modifications = sanitize_html(original)
        scanned += 1
        if apply and sanitized != original:
            path.write_text(sanitized, encoding="utf-8")
            changed.append((path.relative_to(ROOT).as_posix(), modifications))
            original = sanitized
        errors.extend(
            f"{path.relative_to(ROOT).as_posix()}: {error}"
            for error in inspect_html(original)
        )
    if apply:
        print(f"Sanitized {len(changed)} of {scanned} GEO HTML files.")
        for path, count in changed:
            print(f"  {path}: {count} changes")
    if errors:
        print("GEO Audio+ publication check FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"GEO Audio+ publication check PASS ({scanned} HTML files).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true", help="sanitize GEO HTML in place")
    mode.add_argument("--check", action="store_true", help="fail if unsafe claims remain")
    args = parser.parse_args()
    raise SystemExit(run(apply=args.apply))


if __name__ == "__main__":
    main()
