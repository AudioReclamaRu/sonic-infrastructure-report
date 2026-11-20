#!/usr/bin/env python3
"""Rank candidate evidence sources for every sentence in benchmark answer packs.

This is a retrieval diagnostic, not a semantic-entailment checker. A high-ranked
source is only a candidate for human review, not proof that it supports a claim.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    from tools.ai_discovery_retrieval import _bm25_rank, tokenize
except ImportError:
    from ai_discovery_retrieval import _bm25_rank, tokenize

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = "research/ai-visibility-benchmark-queries-2026-11-17.json"
CLAIM_MATRIX = "problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json"
ANSWER_COVERAGE = "problem-solutions/AI_DISCOVERY_ANSWER_COVERAGE_AUDIT_2026-11-20.json"
SOURCE_CLASSES = ("first_party_evidence", "internal_methodology")
SUPPORT_TYPE_CLASSES = {
    "first_party_evidence": ("first_party_evidence",),
    "internal_methodology": ("internal_methodology",),
    "mixed": ("first_party_evidence", "internal_methodology"),
}
CITATION_LINE = re.compile(
    r"^(?:(?:answer\s+)?sources?|источник(?:и)?(?:\s+знаний)?|evidence)\s*:",
    re.IGNORECASE,
)
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?;])\s+(?=[А-Яа-яЁёA-Za-z«„0-9])")


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"required answer-support asset is missing: {relative_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {relative_path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {relative_path}")
    return value


def _safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _source_class(relative_path: str) -> str:
    if Path(relative_path).parts[0] == "evidence":
        return "first_party_evidence"
    return "internal_methodology"


def _required_classes(support_type: str) -> tuple[str, ...]:
    try:
        return SUPPORT_TYPE_CLASSES[support_type]
    except KeyError as exc:
        raise ValueError(f"unsupported claim support_type: {support_type!r}") from exc


def extract_answer_units(content: str, heading: str) -> list[str]:
    """Extract sentence/semicolon units from one Markdown answer section."""
    lines = content.splitlines()
    normalized_heading = heading.strip().lstrip("#").strip()
    heading_index = next(
        (
            index for index, line in enumerate(lines)
            if line.strip() == heading.strip()
            or line.strip().lstrip("#").strip() == normalized_heading
        ),
        None,
    )
    if heading_index is None:
        raise ValueError(f"answer heading does not resolve: {heading!r}")

    units: list[str] = []
    for line in lines[heading_index + 1 :]:
        if line.startswith("## "):
            break
        value = line.strip()
        if not value or value.startswith("<!--"):
            continue
        value = re.sub(r"^[-*]\s+", "", value)
        value = re.sub(r"^>\s*", "", value)
        citation_probe = value.strip("*_ ").strip()
        if CITATION_LINE.match(citation_probe):
            continue

        for fragment in SENTENCE_BOUNDARY.split(value):
            fragment = re.sub(r"\s+", " ", fragment).strip()
            fragment = fragment.strip("*_ ").strip()
            if not fragment or CITATION_LINE.match(fragment):
                continue
            if fragment in {"---", "**Источники**", "**Evidence**"}:
                continue
            units.append(fragment)

    return units


def _build_index(
    documents: list[dict[str, Any]],
    *,
    label: str,
) -> tuple[list[list[str]], dict[str, int], float]:
    if not documents:
        raise ValueError(f"cannot build an empty BM25 index: {label}")
    document_tokens = [tokenize(document["text"]) for document in documents]
    empty_files = [
        documents[index]["file"]
        for index, terms in enumerate(document_tokens)
        if not terms
    ]
    if empty_files:
        raise ValueError(f"{label} documents contain no searchable terms: {empty_files}")
    document_frequency: dict[str, int] = {}
    for terms in document_tokens:
        for term in set(terms):
            document_frequency[term] = document_frequency.get(term, 0) + 1
    average_length = sum(len(terms) for terms in document_tokens) / len(document_tokens)
    return document_tokens, document_frequency, average_length


def _rank_sources(
    query: str,
    documents: list[dict[str, Any]],
) -> tuple[dict[str, int | None], list[dict[str, Any]]]:
    if not documents:
        return {}, []
    document_tokens, document_frequency, average_length = _build_index(
        documents, label="answer assertion source"
    )
    ranked = _bm25_rank(
        query, documents, document_tokens, document_frequency, average_length
    )
    positions = {
        item["file"]: (rank if item["score"] > 0 else None)
        for rank, item in enumerate(ranked, start=1)
    }
    return positions, ranked


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    """Measure source-candidate retrieval for every answer sentence/semicolon unit."""
    benchmark = _read_json(root, BENCHMARK)
    matrix = _read_json(root, CLAIM_MATRIX)
    coverage = _read_json(root, ANSWER_COVERAGE)
    queries = benchmark.get("queries", [])
    matrix_entries = matrix.get("entries", [])
    coverage_entries = coverage.get("entries", [])
    if not all(isinstance(value, list) for value in (queries, matrix_entries, coverage_entries)):
        raise ValueError("benchmark, claim matrix and answer-coverage entries must be lists")

    queries_by_id = {
        item.get("id"): item for item in queries if isinstance(item, dict)
    }
    claims_by_id = {
        item.get("benchmark_query_id"): item
        for item in matrix_entries if isinstance(item, dict)
    }
    coverage_by_id = {
        item.get("benchmark_query_id"): item
        for item in coverage_entries if isinstance(item, dict)
    }
    if len(queries_by_id) != len(queries):
        raise ValueError("benchmark query IDs must be unique")
    if len(claims_by_id) != len(matrix_entries):
        raise ValueError("claim-support query IDs must be unique")
    if len(coverage_by_id) != len(coverage_entries):
        raise ValueError("answer-coverage query IDs must be unique")
    benchmark_ids = set(queries_by_id)
    if set(claims_by_id) != benchmark_ids or set(coverage_by_id) != benchmark_ids:
        raise ValueError("benchmark, claim-support and answer-coverage query IDs must match")

    source_refs = sorted({
        source
        for entry in matrix_entries
        for claim in entry.get("claims", [])
        for source in claim.get("source_refs", [])
        if isinstance(source, str)
    })
    if not source_refs:
        raise ValueError("claim-support matrix has no mapped source documents")

    source_documents: dict[str, dict[str, Any]] = {}
    for relative_path in source_refs:
        if not _safe_relative_path(relative_path):
            raise ValueError(f"unsafe mapped source path: {relative_path!r}")
        try:
            source_text = (root / relative_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read mapped source {relative_path}: {exc}") from exc
        source_documents[relative_path] = {
            "file": relative_path,
            "heading": relative_path,
            "text": relative_path + "\n" + source_text,
            "source_class": _source_class(relative_path),
        }

    documents_by_class = {
        source_class: [
            document for document in source_documents.values()
            if document["source_class"] == source_class
        ]
        for source_class in SOURCE_CLASSES
    }
    class_indexes = {
        source_class: _build_index(
            documents, label=f"{source_class} answer-support source"
        )
        for source_class, documents in documents_by_class.items()
    }

    units: list[dict[str, Any]] = []
    query_unit_counts: dict[str, int] = {}
    for query_id, query in queries_by_id.items():
        claims = claims_by_id[query_id].get("claims", [])
        if not isinstance(claims, list) or not claims:
            raise ValueError(f"query {query_id} has no mapped expected facts")

        claim_documents: list[dict[str, str]] = []
        claims_by_document_id: dict[str, dict[str, Any]] = {}
        for claim in claims:
            fact_index = claim.get("fact_index")
            if not isinstance(fact_index, int) or fact_index < 1:
                raise ValueError(f"query {query_id} has an invalid fact_index")
            refs = claim.get("source_refs")
            if not isinstance(refs, list) or not refs:
                raise ValueError(f"query {query_id} fact {fact_index} has no source_refs")
            missing_refs = [ref for ref in refs if ref not in source_documents]
            if missing_refs:
                raise ValueError(
                    f"query {query_id} fact {fact_index} has unresolved source_refs: {missing_refs}"
                )
            actual_classes = {_source_class(ref) for ref in refs}
            required_classes = set(_required_classes(claim.get("support_type")))
            if actual_classes != required_classes:
                raise ValueError(
                    f"query {query_id} fact {fact_index} source classes "
                    f"{sorted(actual_classes)} do not match support_type "
                    f"{claim.get('support_type')!r}"
                )
            document_id = f"claim:{fact_index}"
            claim_documents.append({
                "file": document_id,
                "heading": document_id,
                "text": " ".join((
                    str(claim.get("expected_fact", "")),
                    str(claim.get("scope_note", "")),
                    str(claim.get("semantic_review_note", "")),
                )),
            })
            claims_by_document_id[document_id] = claim

        claim_tokens, claim_frequency, claim_average_length = _build_index(
            claim_documents, label=f"expected facts for {query_id}"
        )

        answer_entry = coverage_by_id[query_id]
        answer_references: list[tuple[str, dict[str, Any]]] = []
        for field, role in (
            ("answer_references", "primary"),
            ("retrieval_alternatives", "alternative"),
        ):
            values = answer_entry.get(field, [])
            if not isinstance(values, list):
                raise ValueError(f"{query_id} {field} must be a list")
            for item in values:
                if not isinstance(item, dict):
                    raise ValueError(f"{query_id} has an invalid {field} item")
                relative_path = item.get("file")
                heading = item.get("heading")
                if not _safe_relative_path(relative_path) or not isinstance(heading, str) or not heading:
                    raise ValueError(f"{query_id} has an unsafe or incomplete answer reference")
                answer_references.append((role, item))

        unique_references: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
        for role, item in answer_references:
            unique_references.setdefault((item["file"], item["heading"]), (role, item))
        if not unique_references:
            raise ValueError(f"query {query_id} has no answer references")

        unit_number = 0
        for role, answer_ref in unique_references.values():
            answer_file = answer_ref["file"]
            answer_heading = answer_ref["heading"]
            try:
                answer_content = (root / answer_file).read_text(encoding="utf-8")
            except OSError as exc:
                raise ValueError(f"cannot read answer pack {answer_file}: {exc}") from exc
            answer_units = extract_answer_units(answer_content, answer_heading)
            if not answer_units:
                raise ValueError(
                    f"query {query_id} answer heading has no answer text: {answer_heading}"
                )

            for answer_text in answer_units:
                unit_number += 1
                ranked_claims = _bm25_rank(
                    answer_text,
                    claim_documents,
                    claim_tokens,
                    claim_frequency,
                    claim_average_length,
                )
                candidate = next(
                    (item for item in ranked_claims if item["score"] > 0),
                    None,
                )
                is_short_preamble = answer_text.strip().casefold() in {
                    "да.", "нет.", "да", "нет"
                }
                if is_short_preamble:
                    mapping_status = "discourse_preamble"
                    mapping_reason = "short_yes_no_answer_not_treated_as_independent_claim"
                elif candidate:
                    mapping_status = "candidate_match"
                    mapping_reason = "bm25_expected_fact_candidate"
                else:
                    mapping_status = "unmatched_statement"
                    mapping_reason = "no_lexical_expected_fact_candidate"

                unit: dict[str, Any] = {
                    "unit_id": f"{query_id}::{unit_number:02d}",
                    "benchmark_query_id": query_id,
                    "reference_role": role,
                    "answer_file": answer_file,
                    "answer_heading": answer_heading,
                    "answer_text": answer_text,
                    "mapping_status": mapping_status,
                    "mapping_reason": mapping_reason,
                    "manual_review_required": True,
                }
                if candidate:
                    claim = claims_by_document_id[candidate["file"]]
                    fact_index = claim["fact_index"]
                    required_classes = _required_classes(claim["support_type"])
                    mapped_refs = claim["source_refs"]
                    class_ranks: dict[str, int | None] = {}
                    class_candidates: dict[str, list[dict[str, Any]]] = {}
                    for source_class in required_classes:
                        documents = documents_by_class[source_class]
                        tokens, frequency, average_length = class_indexes[source_class]
                        ranked_sources = _bm25_rank(
                            answer_text, documents, tokens, frequency, average_length
                        )
                        mapped_in_class = {
                            ref for ref in mapped_refs
                            if _source_class(ref) == source_class
                        }
                        mapped_rank = next(
                            (
                                rank
                                for rank, result in enumerate(ranked_sources, start=1)
                                if result["file"] in mapped_in_class and result["score"] > 0
                            ),
                            None,
                        )
                        class_ranks[source_class] = mapped_rank
                        class_candidates[source_class] = [
                            {
                                "rank": rank,
                                "file": result["file"],
                                "is_mapped_source": result["file"] in mapped_in_class,
                                "score": round(float(result["score"]), 6),
                            }
                            for rank, result in enumerate(ranked_sources[:5], start=1)
                        ]

                    unit.update({
                        "candidate_fact_index": fact_index,
                        "candidate_expected_fact": claim["expected_fact"],
                        "candidate_fact_score": round(float(candidate["score"]), 6),
                        "support_type": claim["support_type"],
                        "required_source_classes": list(required_classes),
                        "best_mapped_source_rank_by_class": class_ranks,
                        "all_required_classes_top_3": all(
                            class_ranks.get(name) is not None and class_ranks[name] <= 3
                            for name in required_classes
                        ),
                        "all_required_classes_top_5": all(
                            class_ranks.get(name) is not None and class_ranks[name] <= 5
                            for name in required_classes
                        ),
                        "all_required_classes_top_10": all(
                            class_ranks.get(name) is not None and class_ranks[name] <= 10
                            for name in required_classes
                        ),
                        "source_candidates_by_class": class_candidates,
                        "mapped_source_refs_for_candidate_fact": mapped_refs,
                    })
                units.append(unit)

        query_unit_counts[query_id] = unit_number

    matched_units = [unit for unit in units if unit["mapping_status"] == "candidate_match"]
    unmatched_units = [unit for unit in units if unit["mapping_status"] == "unmatched_statement"]
    preambles = [unit for unit in units if unit["mapping_status"] == "discourse_preamble"]
    metrics = {
        "query_count": len(query_unit_counts),
        "answer_unit_count": len(units),
        "units_with_expected_fact_candidate": len(matched_units),
        "units_without_expected_fact_candidate": len(unmatched_units),
        "short_discourse_preambles": len(preambles),
        "candidate_units_all_required_classes_top_3": sum(
            bool(unit.get("all_required_classes_top_3")) for unit in matched_units
        ),
        "candidate_units_all_required_classes_top_5": sum(
            bool(unit.get("all_required_classes_top_5")) for unit in matched_units
        ),
        "candidate_units_all_required_classes_top_10": sum(
            bool(unit.get("all_required_classes_top_10")) for unit in matched_units
        ),
        "candidate_units_by_support_type": {
            support_type: sum(unit.get("support_type") == support_type for unit in matched_units)
            for support_type in SUPPORT_TYPE_CLASSES
        },
        "answer_units_by_query": query_unit_counts,
    }
    return {
        "schema": "studio/ai-discovery-answer-support-candidate-evaluation/1",
        "status": "candidate_retrieval_only",
        "method": (
            "Split each referenced answer section into sentence/semicolon units; "
            "BM25-rank each unit against that query's mapped expected facts; then "
            "rank the selected fact's mapped sources in the complete index for each "
            "source class required by that fact."
        ),
        "metrics": metrics,
        "units": units,
        "weak_units_top_5": [
            unit for unit in matched_units
            if not unit.get("all_required_classes_top_5")
        ],
        "unmatched_units": unmatched_units,
        "limitations": [
            "A BM25 match is a lexical retrieval candidate, not semantic entailment or proof that a source supports the whole sentence.",
            "A sentence may contain multiple assertions; sentence/semicolon segmentation does not replace human atomic-claim review.",
            "Unmatched units may be recommendations, scope limits, citation context or factual claims; they remain unclassified until human review.",
            "A mapped source ranking highly does not prove that it supports the assertion; the source text still requires semantic inspection.",
            "Source ranks are restricted to the repository's mapped corpus and do not measure web-wide discovery.",
            "The diagnostic does not test ChatGPT, Gemini, Perplexity or any external AI platform.",
        ],
    }


def main() -> int:
    try:
        result = evaluate(ROOT)
    except (OSError, ValueError, TypeError) as exc:
        print(f"Answer-support candidate evaluation FAILED: {exc}")
        return 1

    print(
        "ANSWER_SUPPORT_CANDIDATE_BASELINE "
        + json.dumps(result["metrics"], ensure_ascii=False, sort_keys=True)
    )
    for unit in result["weak_units_top_5"]:
        print("ANSWER_SUPPORT_WEAK_UNIT " + json.dumps(unit, ensure_ascii=False, sort_keys=True))
    for unit in result["unmatched_units"]:
        print("ANSWER_SUPPORT_UNMATCHED_UNIT " + json.dumps(unit, ensure_ascii=False, sort_keys=True))
    print("LIMITATION: BM25 candidate ranking is not semantic proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
