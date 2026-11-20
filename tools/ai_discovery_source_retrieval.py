#!/usr/bin/env python3
"""Measure BM25 retrieval of mapped first-party evidence and internal sources."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from tools.ai_discovery_retrieval import _bm25_rank, tokenize
except ImportError:
    from ai_discovery_retrieval import _bm25_rank, tokenize

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = "research/ai-visibility-benchmark-queries-2026-11-17.json"
CLAIM_MATRIX = "problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json"
REPORT = "problem-solutions/AI_DISCOVERY_SOURCE_RETRIEVAL_EVALUATION_2026-11-20.json"
SCHEMA = "studio/ai-discovery-source-retrieval-evaluation/1"


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"required source-retrieval asset is missing: {relative_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {relative_path}: {exc}") from exc
    if not isinstance(result, dict):
        raise ValueError(f"expected JSON object in {relative_path}")
    return result


def _ranked_positions(
    query: str,
    documents: list[dict[str, Any]],
    document_tokens: list[list[str]],
    document_frequency: dict[str, int],
    average_length: float,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    ranked = _bm25_rank(query, documents, document_tokens, document_frequency, average_length)
    positions = {item["file"]: rank for rank, item in enumerate(ranked, start=1)}
    return ranked, positions


def _best_rank(refs: list[str], positions: dict[str, int]) -> int | None:
    ranks = [positions[path] for path in refs if path in positions]
    return min(ranks) if ranks else None


def _count_at(ranks: list[int | None], cutoff: int) -> int:
    return sum(rank is not None and rank <= cutoff for rank in ranks)


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    benchmark = _read_json(root, BENCHMARK)
    matrix = _read_json(root, CLAIM_MATRIX)
    queries = benchmark.get("queries", [])
    matrix_entries = matrix.get("entries", [])
    if not isinstance(queries, list) or not isinstance(matrix_entries, list):
        raise ValueError("benchmark queries and claim matrix entries must be lists")

    queries_by_id = {
        query.get("id"): query for query in queries if isinstance(query, dict)
    }
    claims_by_id = {
        entry.get("benchmark_query_id"): entry
        for entry in matrix_entries if isinstance(entry, dict)
    }
    if len(queries_by_id) != len(queries) or len(claims_by_id) != len(matrix_entries):
        raise ValueError("benchmark and claim matrix IDs must be unique")
    if set(queries_by_id) != set(claims_by_id):
        raise ValueError("claim matrix query IDs do not match the benchmark")

    source_paths = sorted({
        source
        for entry in matrix_entries
        for claim in entry.get("claims", [])
        for source in claim.get("source_refs", [])
        if isinstance(source, str)
    })
    if not source_paths:
        raise ValueError("claim matrix has no source documents")

    documents: list[dict[str, str]] = []
    for relative_path in source_paths:
        path = Path(relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe source path in claim matrix: {relative_path}")
        full_path = root / path
        try:
            source_text = full_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read mapped source {relative_path}: {exc}") from exc
        documents.append({
            "file": relative_path,
            "heading": relative_path,
            "text": relative_path + "\n" + source_text,
        })

    document_tokens = [tokenize(document["text"]) for document in documents]
    if any(not terms for terms in document_tokens):
        empty = [documents[i]["file"] for i, terms in enumerate(document_tokens) if not terms]
        raise ValueError(f"mapped source documents contain no searchable terms: {empty}")
    document_frequency: dict[str, int] = {}
    for terms in document_tokens:
        for term in set(terms):
            document_frequency[term] = document_frequency.get(term, 0) + 1
    average_length = sum(map(len, document_tokens)) / len(document_tokens)

    query_anchor_ranks: list[int | None] = []
    fact_anchor_ranks: list[int | None] = []
    evidence_fact_ranks: list[int | None] = []
    pure_evidence_fact_ranks: list[int | None] = []
    mixed_evidence_fact_ranks: list[int | None] = []
    all_fact_ranks: list[int | None] = []
    entries: list[dict[str, Any]] = []

    for query_id, query in queries_by_id.items():
        matrix_entry = claims_by_id[query_id]
        claims = matrix_entry.get("claims", [])
        if not isinstance(claims, list) or not claims:
            raise ValueError(f"query {query_id} has no claim mappings")

        query_ranked, query_positions = _ranked_positions(
            query.get("query", ""), documents, document_tokens, document_frequency, average_length
        )
        query_refs = sorted({
            ref for claim in claims for ref in claim.get("source_refs", [])
        })
        query_anchor_rank = _best_rank(query_refs, query_positions)
        if query_anchor_rank is None:
            raise ValueError(f"query {query_id} has no resolvable mapped source")
        query_anchor_ranks.append(query_anchor_rank)

        claim_results: list[dict[str, Any]] = []
        for claim in claims:
            fact_text = claim.get("expected_fact", "")
            refs = claim.get("source_refs", [])
            if not isinstance(fact_text, str) or not fact_text.strip() or not isinstance(refs, list) or not refs:
                raise ValueError(f"query {query_id} contains an incomplete claim mapping")
            fact_ranked, fact_positions = _ranked_positions(
                fact_text, documents, document_tokens, document_frequency, average_length
            )
            target_rank = _best_rank(refs, fact_positions)
            if target_rank is None:
                raise ValueError(f"claim in {query_id} has no resolvable source ref")
            fact_anchor_ranks.append(target_rank)
            all_fact_ranks.append(target_rank)

            evidence_refs = [ref for ref in refs if ref.startswith("evidence/")]
            evidence_rank = _best_rank(evidence_refs, fact_positions) if evidence_refs else None
            support_type = claim.get("support_type")
            if evidence_refs:
                evidence_fact_ranks.append(evidence_rank)
                if support_type == "first_party_evidence":
                    pure_evidence_fact_ranks.append(evidence_rank)
                elif support_type == "mixed":
                    mixed_evidence_fact_ranks.append(evidence_rank)

            claim_results.append({
                "fact_index": claim.get("fact_index"),
                "expected_fact": fact_text,
                "support_type": support_type,
                "source_refs": refs,
                "best_mapped_source_rank": target_rank,
                "best_first_party_evidence_rank": evidence_rank,
                "top_candidates": [
                    {
                        "rank": rank,
                        "file": candidate["file"],
                        "score": round(candidate["score"], 6),
                        "is_mapped_source": candidate["file"] in refs,
                    }
                    for rank, candidate in enumerate(fact_ranked[:5], start=1)
                ],
            })

        entries.append({
            "benchmark_query_id": query_id,
            "query": query.get("query", ""),
            "query_best_mapped_source_rank": query_anchor_rank,
            "query_top_candidates": [
                {
                    "rank": rank,
                    "file": candidate["file"],
                    "score": round(candidate["score"], 6),
                    "is_mapped_source": candidate["file"] in query_refs,
                }
                for rank, candidate in enumerate(query_ranked[:5], start=1)
            ],
            "claims": claim_results,
        })

    query_count = len(entries)
    claim_count = len(fact_anchor_ranks)
    evidence_claim_count = len(evidence_fact_ranks)
    query_summaries = [
        {
            "benchmark_query_id": entry["benchmark_query_id"],
            "query_best_mapped_source_rank": entry["query_best_mapped_source_rank"],
            "claims_with_mapped_source_top_3": sum(
                claim["best_mapped_source_rank"] <= 3 for claim in entry["claims"]
            ),
            "claim_count": len(entry["claims"]),
            "first_party_evidence_claims": sum(
                claim["best_first_party_evidence_rank"] is not None for claim in entry["claims"]
            ),
            "first_party_evidence_top_5": sum(
                claim["best_first_party_evidence_rank"] is not None
                and claim["best_first_party_evidence_rank"] <= 5
                for claim in entry["claims"]
            ),
        }
        for entry in entries
    ]
    weak_claims_top_10 = [
        {
            "benchmark_query_id": entry["benchmark_query_id"],
            "fact_index": claim["fact_index"],
            "expected_fact": claim["expected_fact"],
            "support_type": claim["support_type"],
            "best_mapped_source_rank": claim["best_mapped_source_rank"],
            "source_refs": claim["source_refs"],
            "top_candidates": claim["top_candidates"][:5],
        }
        for entry in entries for claim in entry["claims"]
        if claim["best_mapped_source_rank"] > 10
    ]
    weak_evidence_top_5 = [
        {
            "benchmark_query_id": entry["benchmark_query_id"],
            "fact_index": claim["fact_index"],
            "expected_fact": claim["expected_fact"],
            "support_type": claim["support_type"],
            "best_first_party_evidence_rank": claim["best_first_party_evidence_rank"],
            "evidence_refs": [ref for ref in claim["source_refs"] if ref.startswith("evidence/")],
            "top_candidates": claim["top_candidates"][:5],
        }
        for entry in entries for claim in entry["claims"]
        if claim["best_first_party_evidence_rank"] is not None
        and claim["best_first_party_evidence_rank"] > 5
    ]
    weak_pure_evidence_top_5 = [
        item for item in weak_evidence_top_5 if item["support_type"] == "first_party_evidence"
    ]
    weak_mixed_evidence_top_5 = [
        item for item in weak_evidence_top_5 if item["support_type"] == "mixed"
    ]
    all_fact_ranks_by_query = [
        [claim["best_mapped_source_rank"] for claim in entry["claims"]]
        for entry in entries
    ]
    evidence_fact_ranks_by_query = [
        [
            claim["best_first_party_evidence_rank"]
            for claim in entry["claims"]
            if claim["best_first_party_evidence_rank"] is not None
        ]
        for entry in entries
    ]
    metrics = {
        "query_count": query_count,
        "mapped_source_documents": len(documents),
        "queries_with_mapped_source_top_1": _count_at(query_anchor_ranks, 1),
        "queries_with_mapped_source_top_3": _count_at(query_anchor_ranks, 3),
        "queries_with_mapped_source_top_5": _count_at(query_anchor_ranks, 5),
        "max_query_mapped_source_rank": max(rank for rank in query_anchor_ranks if rank is not None),
        "expected_fact_count": claim_count,
        "queries_with_mapped_source_top_1": _count_at(query_anchor_ranks, 1),
        "queries_with_mapped_source_top_3": _count_at(query_anchor_ranks, 3),
        "queries_with_mapped_source_top_5": _count_at(query_anchor_ranks, 5),
        "claims_with_mapped_source_top_1": _count_at(fact_anchor_ranks, 1),
        "claims_with_mapped_source_top_3": _count_at(fact_anchor_ranks, 3),
        "claims_with_mapped_source_top_5": _count_at(fact_anchor_ranks, 5),
        "claims_with_mapped_source_top_10": _count_at(fact_anchor_ranks, 10),
        "claims_with_first_party_evidence": evidence_claim_count,
        "pure_first_party_claim_count": len(pure_evidence_fact_ranks),
        "pure_first_party_evidence_top_3": _count_at(pure_evidence_fact_ranks, 3),
        "pure_first_party_evidence_top_5": _count_at(pure_evidence_fact_ranks, 5),
        "pure_first_party_evidence_top_10": _count_at(pure_evidence_fact_ranks, 10),
        "mixed_claim_count": len(mixed_evidence_fact_ranks),
        "mixed_claim_evidence_top_3": _count_at(mixed_evidence_fact_ranks, 3),
        "mixed_claim_evidence_top_5": _count_at(mixed_evidence_fact_ranks, 5),
        "mixed_claim_evidence_top_10": _count_at(mixed_evidence_fact_ranks, 10),
        "evidence_claims_with_evidence_top_1": _count_at(evidence_fact_ranks, 1),
        "evidence_claims_with_evidence_top_3": _count_at(evidence_fact_ranks, 3),
        "evidence_claims_with_evidence_top_5": _count_at(evidence_fact_ranks, 5),
        "evidence_claims_with_evidence_top_10": _count_at(evidence_fact_ranks, 10),
        "all_claims_have_mapped_source_top_3": sum(
            all(rank is not None and rank <= 3 for rank in [
                claim["best_mapped_source_rank"] for claim in entry["claims"]
            ]) for entry in entries
        ),
        "all_claims_have_mapped_source_top_5": sum(
            all(claim["best_mapped_source_rank"] <= 5 for claim in entry["claims"])
            for entry in entries
        ),
        "all_claims_have_mapped_source_top_10": sum(
            all(claim["best_mapped_source_rank"] <= 10 for claim in entry["claims"])
            for entry in entries
        ),
        "all_evidence_claims_have_evidence_top_5": sum(
            bool(ranks) and all(rank is not None and rank <= 5 for rank in ranks)
            for ranks in evidence_fact_ranks_by_query
        ),
        "all_evidence_claims_have_evidence_top_10": sum(
            bool(ranks) and all(rank is not None and rank <= 10 for rank in ranks)
            for ranks in evidence_fact_ranks_by_query
        ),
        "max_mapped_source_rank": max(rank for rank in fact_anchor_ranks if rank is not None),
        "median_mapped_source_rank": sorted(rank for rank in fact_anchor_ranks if rank is not None)[
            len(fact_anchor_ranks) // 2
        ],
    }
    return {
        "schema": SCHEMA,
        "date": "2026-11-20",
        "status": "diagnostic_source_retrieval_baseline",
        "method": {
            "name": "BM25",
            "k1": 1.2,
            "b": 0.75,
            "tokenizer": "Same fixed Russian/English tokenizer and light stemming as the answer-pack baseline.",
            "query_modes": [
                "Original benchmark question against all mapped source documents.",
                "Each exact expected_fact separately against all mapped source documents.",
            ],
            "source_classes": "First-party evidence files under evidence/ are measured separately from internal-methodology and entity/canon sources.",
            "scope": "The 44 unique documents explicitly mapped to the 112 claims in the claim-support matrix.",
            "not_a_claim": "This is not a production retriever, an external AI-platform test or a measurement of AI visibility.",
        },
        "corpus": {
            "document_count": len(documents),
            "documents": source_paths,
        },
        "metrics": metrics,
        "entries": entries,
        "query_summaries": query_summaries,
        "weak_claims_top_10": weak_claims_top_10,
        "weak_evidence_top_5": weak_evidence_top_5,
        "weak_pure_evidence_top_5": weak_pure_evidence_top_5,
        "weak_mixed_evidence_top_5": weak_mixed_evidence_top_5,
        "limitations": [
            "Source relevance is evaluated against both the user query and the fact-specific expected text; the latter is a controlled diagnostic, not text supplied by an actual searcher.",
            "A claim may map to multiple documents; the best mapped-document rank is reported and does not prove that every mapped source is needed.",
            "First-party evidence records are dated snapshots with the scope and crawl-freshness limits stated in the records.",
            "Internal methodology, entity records and canon documents are not public evidence and are not treated as independent verification.",
            "BM25 is lexical. A low score may reflect paraphrase or vocabulary mismatch, not a false source mapping.",
            "The candidate corpus is restricted to 44 source documents already mapped in the claim-support matrix; unmapped repository files are not searched.",
        ],
    }


def validate_report(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        expected = evaluate(root)
        actual = _read_json(root, REPORT)
    except ValueError as exc:
        return [str(exc)]
    if actual.get("schema") != SCHEMA:
        errors.append("unexpected AI Discovery source-retrieval evaluation schema")
    for field in ("date", "status", "method", "corpus", "metrics"):
        if actual.get(field) != expected.get(field):
            errors.append(f"AI Discovery source-retrieval baseline is stale or inconsistent: {field}")
    if actual.get("baseline_review_status") != "reviewed":
        errors.append("AI Discovery source-retrieval baseline must be marked reviewed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the deterministic evaluation JSON")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    args = parser.parse_args()
    result = evaluate(args.root)
    if args.write:
        output = args.root / REPORT
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {REPORT}")
    metrics = result["metrics"]
    print("SOURCE_RETRIEVAL_METRICS " + json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    print(
        "AI Discovery mapped-source retrieval: "
        f"{metrics['queries_with_mapped_source_top_3']}/{metrics['query_count']} queries have a mapped source in top-3; "
        f"{metrics['claims_with_mapped_source_top_5']}/{metrics['expected_fact_count']} fact claims have a mapped source in top-5; "
        f"first-party evidence top-5 across all (including mixed) claims: {metrics['evidence_claims_with_evidence_top_5']}/{metrics['claims_with_first_party_evidence']}; "
        f"pure first-party claims evidence top-5: {metrics['pure_first_party_evidence_top_5']}/{metrics['pure_first_party_claim_count']}; "
        f"mixed claims with evidence top-5: {metrics['mixed_claim_evidence_top_5']}/{metrics['mixed_claim_count']}; "
        f"all facts are covered at top-5 in {metrics['all_claims_have_mapped_source_top_5']}/{metrics['query_count']} queries; "
        f"query-level mapped source top-3: {metrics['queries_with_mapped_source_top_3']}/{metrics['query_count']}; "
        f"all facts top-5: {metrics['all_claims_have_mapped_source_top_5']}/{metrics['query_count']}; "
        f"max fact rank={metrics['max_mapped_source_rank']}; "
        f"weak facts outside top-10={len(result['weak_claims_top_10'])}; "
        f"first-party evidence outside top-5={len(result['weak_evidence_top_5'])}."
    )
    for weak in result["weak_claims_top_10"]:
        print(
            "SOURCE_RETRIEVAL_WEAK_FACT "
            + json.dumps(weak, ensure_ascii=False, sort_keys=True)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
