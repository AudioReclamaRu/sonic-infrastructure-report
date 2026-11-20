#!/usr/bin/env python3
"""Build a text-first review inventory for low-ranked mapped answer sources.

The inventory is an AI-Discoverability diagnostic: it exposes where answer
phrases fail to surface their already-mapped public/internal sources. A lexical
rank is never treated as semantic support or as an external AI visibility result.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from tools.ai_discovery_answer_support import (
        CLAIM_MATRIX,
        ROOT,
        _build_index,
        _read_json,
        _safe_relative_path,
        _source_class,
        evaluate as evaluate_answer_support,
    )
    from tools.ai_discovery_retrieval import _bm25_rank, tokenize
except ImportError:
    from ai_discovery_answer_support import (
        CLAIM_MATRIX,
        ROOT,
        _build_index,
        _read_json,
        _safe_relative_path,
        _source_class,
        evaluate as evaluate_answer_support,
    )
    from ai_discovery_retrieval import _bm25_rank, tokenize

JSON_REPORT = "research/AI_DISCOVERY_ANSWER_SUPPORT_LOW_RANK_INVENTORY_2026-11-20.json"
MD_REPORT = "research/AI_DISCOVERY_ANSWER_SUPPORT_LOW_RANK_INVENTORY_2026-11-20.md"
URL_RE = re.compile(r"https?://[^\s)>]+", re.IGNORECASE)
FRONT_MATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def _source_passages(content: str) -> list[str]:
    """Return compact source paragraphs; keep headings attached as context."""
    body = FRONT_MATTER_RE.sub("", content, count=1)
    passages: list[str] = []
    current_heading = ""
    for block in re.split(r"\n\s*\n", body):
        value = re.sub(r"\s+", " ", block).strip()
        if not value:
            continue
        if value.startswith("#"):
            current_heading = value[:180]
            continue
        if len(value) < 35:
            continue
        if current_heading:
            value = current_heading + " — " + value
        passages.append(value[:1100])
    return passages


def _passage_candidates(answer_text: str, source_text: str, limit: int = 2) -> list[dict[str, Any]]:
    query_terms = set(tokenize(answer_text))
    passages = _source_passages(source_text)
    ranked = []
    for index, passage in enumerate(passages):
        terms = set(tokenize(passage))
        overlap = sorted(query_terms & terms)
        ranked.append({
            "passage_index": index,
            "overlap_term_count": len(overlap),
            "overlap_terms": overlap[:20],
            "text": passage,
        })
    ranked.sort(key=lambda item: (-item["overlap_term_count"], item["passage_index"]))
    chosen = ranked[:limit]
    if chosen and chosen[0]["overlap_term_count"] == 0:
        return [{
            "passage_index": chosen[0]["passage_index"],
            "overlap_term_count": 0,
            "overlap_terms": [],
            "text": chosen[0]["text"],
            "selection_note": "first available paragraph shown because no lexical overlap was found",
        }]
    return chosen


def _source_metadata(path: str, content: str) -> dict[str, Any]:
    evidence_id = re.search(r"^id:\s*(.+?)\s*$", content, re.MULTILINE)
    observed_date = re.search(r"^(?:date|observed):\s*(.+?)\s*$", content, re.MULTILINE)
    status = re.search(r"^status:\s*(.+?)\s*$", content, re.MULTILINE)
    primary_urls = URL_RE.findall("\n".join(
        line for line in content.splitlines()
        if "Primary source" in line or "Primary sources" in line
    ))
    return {
        "source_class": _source_class(path),
        "evidence_id": evidence_id.group(1) if evidence_id else None,
        "record_date": observed_date.group(1) if observed_date else None,
        "record_status": status.group(1) if status else None,
        "primary_source_urls": primary_urls,
    }


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    """Recompute exact mapped-source ranks and attach source-text excerpts."""
    support = evaluate_answer_support(root)
    weak_units = support["manual_disposition_weak_rank_units"]
    matrix = _read_json(root, CLAIM_MATRIX)
    refs = sorted({
        ref
        for entry in matrix.get("entries", [])
        for claim in entry.get("claims", [])
        for ref in claim.get("source_refs", [])
    })
    if not refs:
        raise ValueError("claim-support matrix has no mapped source documents")

    source_documents: dict[str, dict[str, Any]] = {}
    for ref in refs:
        if not _safe_relative_path(ref):
            raise ValueError(f"unsafe mapped source path: {ref!r}")
        try:
            content = (root / ref).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read mapped source {ref}: {exc}") from exc
        source_documents[ref] = {
            "file": ref,
            "heading": ref,
            "text": ref + "\n" + content,
            "content": content,
            "source_class": _source_class(ref),
        }

    documents_by_class = {
        name: [item for item in source_documents.values() if item["source_class"] == name]
        for name in ("first_party_evidence", "internal_methodology")
    }
    indexes = {
        name: _build_index(items, label=f"{name} low-rank review")
        for name, items in documents_by_class.items()
        if items
    }

    units: list[dict[str, Any]] = []
    channel_count = 0
    channel_top5_count = 0
    category_counts: Counter[str] = Counter()
    for unit in weak_units:
        answer_text = unit["answer_text"]
        mapped_refs = unit["mapped_source_refs_for_unit"]
        required_classes = unit["required_source_classes"]
        source_reviews = []
        class_ranks: dict[str, int | None] = {}
        for source_class in required_classes:
            docs = documents_by_class[source_class]
            tokens, frequency, average_length = indexes[source_class]
            ranked = _bm25_rank(answer_text, docs, tokens, frequency, average_length)
            rank_by_file = {
                item["file"]: (position if item["score"] > 0 else None)
                for position, item in enumerate(ranked, start=1)
            }
            mapped_for_class = [
                ref for ref in mapped_refs
                if source_documents[ref]["source_class"] == source_class
            ]
            if not mapped_for_class:
                raise ValueError(f"{unit['unit_id']} has no mapped source in required class {source_class}")
            best_rank = min(
                (rank_by_file.get(ref) for ref in mapped_for_class if rank_by_file.get(ref) is not None),
                default=None,
            )
            class_ranks[source_class] = best_rank
            channel_count += 1
            if best_rank is not None and best_rank <= 5:
                channel_top5_count += 1
            candidate_list = [
                {
                    "rank": position,
                    "file": item["file"],
                    "mapped_for_unit": item["file"] in mapped_for_class,
                    "score": round(float(item["score"]), 6),
                }
                for position, item in enumerate(ranked[:5], start=1)
            ]
            source_reviews.append({
                "source_class": source_class,
                "best_mapped_rank": best_rank,
                "mapped_sources": [
                    {
                        "path": ref,
                        "lexical_rank": rank_by_file.get(ref),
                        "metadata": _source_metadata(ref, source_documents[ref]["content"]),
                        "text_excerpt_candidates": _passage_candidates(
                            answer_text, source_documents[ref]["content"]
                        ),
                    }
                    for ref in mapped_for_class
                ],
                "top_5_candidates": candidate_list,
            })

        category = unit["unit_disposition"]["category"]
        category_counts[category] += 1
        units.append({
            "unit_id": unit["unit_id"],
            "benchmark_query_id": unit["benchmark_query_id"],
            "reference_role": unit["reference_role"],
            "answer_file": unit["answer_file"],
            "answer_heading": unit["answer_heading"],
            "answer_text": answer_text,
            "category": category,
            "review_date": unit["unit_disposition"]["review_date"],
            "existing_manual_review_note": unit["unit_disposition"]["review_note"],
            "required_source_classes": required_classes,
            "mapped_source_refs": mapped_refs,
            "best_mapped_source_rank_by_class": class_ranks,
            "lexical_diagnosis": (
                "no_positive_lexical_match_in_at_least_one_required_class"
                if any(value is None for value in class_ranks.values())
                else "mapped_source_below_top_5_in_at_least_one_required_class"
            ),
            "semantic_verdict": "pending_manual_source_text_review",
            "source_reviews": source_reviews,
        })

    retrieval_count = support["metrics"]["manual_disposition_retrieval_unit_count"]
    if len(units) > retrieval_count:
        raise ValueError("low-rank unit count exceeds the retrieval-required denominator")
    if len({unit["unit_id"] for unit in units}) != len(units):
        raise ValueError("low-rank review contains duplicate unit IDs")

    return {
        "schema": "studio/ai-discovery-low-rank-answer-support-inventory/1",
        "date": "2026-11-20",
        "status": "lexical_inventory_pending_semantic_review",
        "purpose": (
            "Prioritize source-text checks that can improve AI answer retrieval and "
            "recommendation quality. This is not a semantic verdict or external visibility measurement."
        ),
        "method": {
            "source_ranker": "same BM25 tokenizer, corpus and parameters as ai_discovery_answer_support.py",
            "excerpt_selection": "paragraphs selected by lexical term overlap; excerpt selection is navigation support only",
            "semantic_review": "not performed by this tool; every unit is explicitly pending manual source-text review",
        },
        "metrics": {
            "benchmark_query_count": support["metrics"]["query_count"],
            "answer_unit_count": support["metrics"]["answer_unit_count"],
            "manual_disposition_unit_count": support["metrics"]["manual_disposition_unit_count"],
            "retrieval_required_unit_count": retrieval_count,
            "no_retrieval_unit_count": support["metrics"]["manual_disposition_no_retrieval_unit_count"],
            "units_with_expected_fact_candidate": support["metrics"]["units_with_expected_fact_candidate"],
            "units_without_expected_fact_candidate": support["metrics"]["units_without_expected_fact_candidate"],
            "candidate_units_all_required_classes_top_3": support["metrics"]["candidate_units_all_required_classes_top_3"],
            "candidate_units_all_required_classes_top_5": support["metrics"]["candidate_units_all_required_classes_top_5"],
            "candidate_units_all_required_classes_top_10": support["metrics"]["candidate_units_all_required_classes_top_10"],
            "low_rank_unit_count": len(units),
            "retrieval_units_with_mapped_sources_top_5": retrieval_count - len(units),
            "retrieval_units_top_5_coverage": round((retrieval_count - len(units)) / max(retrieval_count, 1), 6),
            "required_source_channel_count": channel_count,
            "required_source_channels_top_5": channel_top5_count,
            "low_rank_by_category": dict(sorted(category_counts.items())),
        },
        "units": units,
        "limitations": [
            "BM25 rank measures lexical visibility inside the mapped repository corpus, not semantic entailment.",
            "A top-ranked source may still fail to support a claim; a low-ranked source may support it fully.",
            "Excerpt selection uses word overlap and is only a reading aid, not an automated semantic judgment.",
            "The repository corpus is not the public web and does not measure what ChatGPT, Gemini, Perplexity or other systems retrieve.",
            "All 46 external benchmark prompts remain not_run until executed on the target platforms and market context.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "---",
        "type: ai-discovery-low-rank-answer-support-inventory",
        "date: 2026-11-20",
        "lang: ru",
        "status: lexical_inventory_pending_semantic_review",
        "---",
        "",
        "# Реестр низкоранговых источниковых привязок — 20.11.2026",
        "",
        "## Зачем нужен этот реестр",
        "",
        "Реестр помогает проверить, почему уже назначенный источник плохо обнаруживается лексическим retrieval для конкретной фразы. Он нужен для улучшения доступности и точности AI-ответов, а не для искусственного повышения BM25.",
        "",
        "## Метрики и знаменатели",
        "",
        f"- Размечено единиц: **{metrics['manual_disposition_unit_count']}/{metrics['answer_unit_count']}**.",
        f"- Требуют retrieval: **{metrics['retrieval_required_unit_count']}**; без retrieval: **{metrics['no_retrieval_unit_count']}**.",
        f"- Низкоранговых единиц: **{metrics['low_rank_unit_count']}/{metrics['retrieval_required_unit_count']}**.",
        f"- Единиц с назначенными источниками в top-5: **{metrics['retrieval_units_with_mapped_sources_top_5']}/{metrics['retrieval_required_unit_count']}** ({metrics['retrieval_units_top_5_coverage']:.1%}).",
        f"- Среди единиц с expected-fact candidate все обязательные классы в top-3/top-5/top-10: **{metrics['candidate_units_all_required_classes_top_3']}/{metrics['units_with_expected_fact_candidate']}**, **{metrics['candidate_units_all_required_classes_top_5']}/{metrics['units_with_expected_fact_candidate']}**, **{metrics['candidate_units_all_required_classes_top_10']}/{metrics['units_with_expected_fact_candidate']}**.",
        "",
        "Эти метрики имеют разные знаменатели и не должны сравниваться как одна последовательность.",
        "",
        "## Карточки для ручной проверки",
        "",
    ]
    for unit in report["units"]:
        lines.extend([
            f"### {unit['unit_id']} — {unit['category']}",
            "",
            f"**Запрос:** {unit['benchmark_query_id']}  ",
            f"**Фраза:** {unit['answer_text']}  ",
            f"**Диагностика:** {unit['lexical_diagnosis']}  ",
            f"**Назначенные источники:** {', '.join(unit['mapped_source_refs'])}",
            "",
        ])
        for source in unit["source_reviews"]:
            lines.append(
                f"**Канал {source['source_class']} — лучший назначенный ранг: "
                f"{source['best_mapped_rank'] if source['best_mapped_rank'] is not None else 'нет положительного совпадения'}**"
            )
            for mapped in source["mapped_sources"]:
                lines.append(f"- {mapped['path']} — ранг: {mapped['lexical_rank']}")
                for excerpt in mapped["text_excerpt_candidates"]:
                    lines.append(f"  - Фрагмент источника: {excerpt['text']}")
            lines.append("")
        lines.extend([
            f"**Прежняя ручная заметка:** {unit['existing_manual_review_note']}",
            "",
            "**Семантический вердикт:** ожидает ручной проверки текста источника.",
            "",
        ])
    lines.extend([
        "## Ограничения",
        "",
        "- Ранг BM25 не является доказательством смысловой поддержки.",
        "- Выдержки подобраны по лексическому пересечению и служат навигацией; при нулевом пересечении показывается первый содержательный абзац.",
        "- Реестр не измеряет внешнюю AI-Discoverability. Все внешние benchmark-запросы остаются not_run до фактического тестирования.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write JSON and Markdown inventories")
    args = parser.parse_args()
    report = evaluate(ROOT)
    if args.write:
        json_path = ROOT / JSON_REPORT
        md_path = ROOT / MD_REPORT
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"Wrote {JSON_REPORT} and {MD_REPORT}")
    else:
        print(json.dumps(report["metrics"], ensure_ascii=False, sort_keys=True))
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
