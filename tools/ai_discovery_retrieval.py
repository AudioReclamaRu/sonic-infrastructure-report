#!/usr/bin/env python3
"""Deterministic lexical retrieval diagnostic for internal AI Discovery answer packs.

This is a BM25 baseline over answer-pack sections. It is not an embedding model,
a production retriever, or a measurement of any external AI platform.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = "research/ai-visibility-benchmark-queries-2026-11-17.json"
ANSWER_COVERAGE = "problem-solutions/AI_DISCOVERY_ANSWER_COVERAGE_AUDIT_2026-11-20.json"
REPORT = "problem-solutions/AI_DISCOVERY_RETRIEVAL_EVALUATION_2026-11-20.json"
SCHEMA = "studio/ai-discovery-retrieval-evaluation/1"

TOKEN_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
STOPWORDS = set("""
а без более бы был была были быть в вам вас весь во вот все всего всех вы где да даже для до
его ее если есть ещё же за здесь и из или им их к как ко когда кто ли либо мне может мы на
над наш не него нее нет ни них но ну о об один она они оно от очень по под при про раз с со
так такая такие такой там те то того тоже той только том ты у уже что чтобы эта это этот я
свой своя свои своего свою каждый каждую которые который которая которых котором каков куда
надо нужно можно друг друга также отдельно именно после перед между несколько какой какие
каким каким-то чем чей чья чье чьи the and or to of for in on at is are be this that with from
how what which who does can do a an as by into about
""".split())
LONG_SUFFIXES = (
    "иями", "ями", "ами", "его", "ому", "ыми", "ими", "ого", "ему",
    "ией", "ей", "ов", "ев", "ам", "ям", "ах", "ях", "ы", "и",
    "а", "я", "е", "у", "ю", "о",
)
SHORT_SUFFIXES = (
    "ами", "ями", "ого", "ому", "ее", "ая", "ое", "ые", "ых",
    "ий", "ый", "ой", "ей", "ам", "ям", "ах", "ях", "ов",
    "ев", "ы", "и", "а", "я", "е", "у", "ю", "о",
)


def _stem(token: str) -> str:
    token = token.lower().replace("ё", "е")
    if len(token) > 6:
        for suffix in LONG_SUFFIXES:
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                return token[:-len(suffix)]
    elif len(token) > 4:
        for suffix in SHORT_SUFFIXES:
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                return token[:-len(suffix)]
    return token


def tokenize(text: str) -> list[str]:
    """Tokenize Russian/English text, remove common stopwords and light-stem."""
    tokens = TOKEN_RE.findall(text.lower().replace("ё", "е"))
    return [
        _stem(token)
        for token in tokens
        if len(token) > 2 and token not in STOPWORDS
    ]


def extract_sections(path: str, content: str) -> list[dict[str, str]]:
    """Extract H2 answer sections; exclude pack-level usage instructions."""
    lines = content.splitlines()
    sections: list[dict[str, str]] = []
    start: int | None = None
    heading = ""
    body: list[str] = []

    def flush() -> None:
        if start is None or heading.lower().startswith("правило использования"):
            return
        sections.append({
            "file": path,
            "heading": heading,
            "text": heading + "\n" + "\n".join(body),
        })

    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            flush()
            start = 1
            heading = match.group(1).strip()
            body = []
        elif start is not None:
            body.append(line)
    flush()
    return sections


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"required retrieval asset is missing: {relative_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {relative_path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {relative_path}")
    return value


def _reference_key(reference: dict[str, str]) -> tuple[str, str]:
    heading = reference.get("heading", "")
    heading = re.sub(r"^#+\s*", "", heading).strip()
    return reference.get("file", ""), heading


def _bm25_rank(
    query: str,
    documents: list[dict[str, Any]],
    document_tokens: list[list[str]],
    document_frequency: dict[str, int],
    average_length: float,
) -> list[dict[str, Any]]:
    count = len(documents)
    query_terms = set(tokenize(query))
    ranked: list[dict[str, Any]] = []
    k1, b = 1.2, 0.75

    for index, document in enumerate(documents):
        terms = document_tokens[index]
        term_frequency: dict[str, int] = {}
        for term in terms:
            term_frequency[term] = term_frequency.get(term, 0) + 1
        length = len(terms)
        score = 0.0
        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if not frequency:
                continue
            df = document_frequency.get(term, 0)
            inverse_document_frequency = math.log(
                1.0 + (count - df + 0.5) / (df + 0.5)
            )
            denominator = frequency + k1 * (
                1.0 - b + b * length / max(average_length, 1.0)
            )
            score += (
                inverse_document_frequency
                * frequency
                * (k1 + 1.0)
                / denominator
            )
        ranked.append({
            "file": document["file"],
            "heading": document["heading"],
            "score": score,
        })

    ranked.sort(key=lambda item: (-item["score"], item["file"], item["heading"]))
    return ranked


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    """Run the BM25 diagnostic against the answer sections referenced by the audit."""
    benchmark = _read_json(root, BENCHMARK)
    coverage = _read_json(root, ANSWER_COVERAGE)
    queries = benchmark.get("queries", [])
    coverage_entries = coverage.get("entries", [])
    if not isinstance(queries, list) or not isinstance(coverage_entries, list):
        raise ValueError("benchmark queries and answer-coverage entries must be lists")

    coverage_by_id = {
        entry.get("benchmark_query_id"): entry
        for entry in coverage_entries
        if isinstance(entry, dict)
    }
    if len(coverage_by_id) != len(coverage_entries):
        raise ValueError("answer-coverage entries must have unique query IDs")
    benchmark_ids = {query.get("id") for query in queries if isinstance(query, dict)}
    if benchmark_ids != set(coverage_by_id):
        raise ValueError("answer-coverage query IDs do not match the benchmark")

    answer_files: set[str] = set()
    for entry in coverage_entries:
        for field in ("answer_references", "retrieval_alternatives"):
            refs = entry.get(field, [])
            if not isinstance(refs, list):
                raise ValueError(f"{field} must be a list for {entry.get('benchmark_query_id')}")
            for reference in refs:
                if not isinstance(reference, dict):
                    raise ValueError(f"invalid answer reference for {entry.get('benchmark_query_id')}")
                relative_path = reference.get("file", "")
                if not relative_path or Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
                    raise ValueError(f"unsafe answer reference path: {relative_path!r}")
                answer_files.add(relative_path)

    documents: list[dict[str, str]] = []
    for relative_path in sorted(answer_files):
        full_path = root / relative_path
        try:
            content = full_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read answer pack {relative_path}: {exc}") from exc
        documents.extend(extract_sections(relative_path, content))

    if not documents:
        raise ValueError("retrieval candidate corpus is empty")

    document_tokens = [tokenize(document["text"]) for document in documents]
    document_frequency: dict[str, int] = {}
    for terms in document_tokens:
        for term in set(terms):
            document_frequency[term] = document_frequency.get(term, 0) + 1
    average_length = sum(map(len, document_tokens)) / len(document_tokens)

    results: list[dict[str, Any]] = []
    primary_top1 = 0
    primary_top3 = 0
    acceptable_top1 = 0
    acceptable_top3 = 0
    reciprocal_ranks: list[float] = []

    for query in queries:
        query_id = query.get("id")
        coverage_entry = coverage_by_id[query_id]
        primary_refs = coverage_entry.get("answer_references", [])
        alternatives = coverage_entry.get("retrieval_alternatives", [])
        if not primary_refs:
            raise ValueError(f"query {query_id} has no primary answer reference")

        ranked = _bm25_rank(
            query.get("query", ""),
            documents,
            document_tokens,
            document_frequency,
            average_length,
        )
        positions = {
            (item["file"], item["heading"]): rank
            for rank, item in enumerate(ranked, start=1)
        }
        primary_keys = [_reference_key(ref) for ref in primary_refs]
        alternative_keys = [_reference_key(ref) for ref in alternatives]
        target_keys = primary_keys + alternative_keys
        unresolved = [key for key in target_keys if key not in positions]
        if unresolved:
            raise ValueError(f"query {query_id} has unresolved retrieval targets: {unresolved}")

        primary_rank = min(positions[key] for key in primary_keys)
        acceptable_rank = min(positions[key] for key in target_keys)
        primary_top1 += int(primary_rank == 1)
        primary_top3 += int(primary_rank <= 3)
        acceptable_top1 += int(acceptable_rank == 1)
        acceptable_top3 += int(acceptable_rank <= 3)
        reciprocal_ranks.append(1.0 / primary_rank)

        results.append({
            "benchmark_query_id": query_id,
            "query": query.get("query", ""),
            "primary_answer_references": primary_refs,
            "retrieval_alternatives": alternatives,
            "primary_target_rank": primary_rank,
            "acceptable_target_rank": acceptable_rank,
            "top_candidates": [
                {
                    "rank": rank,
                    "file": candidate["file"],
                    "heading": candidate["heading"],
                    "score": round(candidate["score"], 6),
                }
                for rank, candidate in enumerate(ranked[:3], start=1)
            ],
        })

    query_count = len(results)
    return {
        "schema": SCHEMA,
        "date": "2026-11-20",
        "status": "diagnostic_lexical_baseline",
        "method": {
            "name": "BM25",
            "k1": 1.2,
            "b": 0.75,
            "tokenizer": "Unicode Russian/English tokenization, common stopword removal, light Russian suffix stemming",
            "scope": "Only answer sections in the five internal evaluator-side answer packs referenced by the answer-coverage audit.",
            "not_a_claim": "This is not a production retriever, embedding benchmark, external AI-platform test or measurement of AI visibility.",
        },
        "corpus": {
            "answer_file_count": len(answer_files),
            "candidate_section_count": len(documents),
            "answer_files": sorted(answer_files),
        },
        "metrics": {
            "query_count": query_count,
            "primary_top_1": primary_top1,
            "primary_top_3": primary_top3,
            "acceptable_top_1": acceptable_top1,
            "acceptable_top_3": acceptable_top3,
            "primary_mrr": round(sum(reciprocal_ranks) / max(query_count, 1), 6),
        },
        "entries": results,
        "limitations": [
            "The candidate corpus is deliberately limited to internal answer-pack sections; primary evidence pages and the wider repository knowledge corpus are not ranked here.",
            "The tokenizer and stemmer are lightweight deterministic heuristics, not a Russian morphological analyzer.",
            "Explicit retrieval alternatives are accepted only when separately documented and resolved; they do not replace the canonical answer route.",
            "A lexical rank does not predict semantic retrieval by a particular commercial AI model.",
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
        errors.append("unexpected AI Discovery retrieval evaluation schema")
    for field in ("date", "status", "method", "corpus", "metrics", "entries", "limitations"):
        if actual.get(field) != expected.get(field):
            errors.append(f"AI Discovery retrieval evaluation is stale or inconsistent: {field}")
    metrics = expected["metrics"]
    if metrics["acceptable_top_1"] != metrics["query_count"]:
        errors.append("every benchmark query must have an acceptable answer in BM25 top-1")
    if metrics["primary_top_3"] != metrics["query_count"]:
        errors.append("every canonical answer must appear in BM25 top-3")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the deterministic evaluation JSON")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    args = parser.parse_args()
    result = evaluate(args.root)
    output_path = args.root / REPORT
    if args.write:
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {REPORT}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    metrics = result["metrics"]
    print(
        "AI Discovery lexical retrieval diagnostic: "
        f"{metrics['acceptable_top_1']}/{metrics['query_count']} acceptable top-1, "
        f"{metrics['primary_top_1']}/{metrics['query_count']} canonical top-1, "
        f"{metrics['primary_top_3']}/{metrics['query_count']} canonical top-3 "
        f"across {result['corpus']['candidate_section_count']} answer sections."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
