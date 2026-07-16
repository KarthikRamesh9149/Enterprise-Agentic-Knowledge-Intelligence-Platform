"""Real retrieval evaluation over the shipped demo corpus.

The previous ``/evals/run`` ignored the bundled ``demo-data/eval-*.jsonl``
datasets, scored 2 hardcoded questions against a mock LLM that always emits
``[C#]`` citations, and used a trivially-passable threshold — so it always
passed. This module instead loads the shipped eval cases (which carry
``expected_documents`` ground truth) and measures the REAL embedding
retrieval: recall@k of the expected document and keyword grounding of the
retrieved text. It is pure/offline (no pgvector, no DB), so it runs in CI and
can genuinely fail.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from app.services.providers import get_embedding_provider

DEFAULT_TOP_K = 5


def _demo_dir() -> Path:
    """Locate the shipped demo-data directory robustly.

    It lives at the repo root, but the CI installs the package non-editably
    (so __file__ is under site-packages) and runs from the backend/ dir, so we
    search upward from both the source file and the cwd for a demo-data dir.
    """
    anchors = [Path(__file__).resolve(), Path.cwd().resolve()]
    for anchor in anchors:
        for parent in [anchor, *anchor.parents]:
            candidate = parent / "demo-data"
            if candidate.is_dir():
                return candidate
    # Fall back to the original relative guess.
    return Path(__file__).resolve().parents[3] / "demo-data"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    an = math.sqrt(sum(x * x for x in a)) or 1.0
    bn = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (an * bn)


def load_eval_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(_demo_dir().glob("eval-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def build_corpus() -> list[dict[str, Any]]:
    """Chunk every demo .md document and embed each chunk (real provider)."""
    embed = get_embedding_provider().embed
    corpus: list[dict[str, Any]] = []
    for path in sorted(_demo_dir().glob("*.md")):
        paragraphs = [p.strip() for p in path.read_text(encoding="utf-8").split("\n\n")]
        for para in paragraphs:
            if len(para) < 40:  # skip headings / tiny fragments
                continue
            corpus.append({"document_name": path.name, "content": para, "embedding": embed(para)})
    return corpus


def score_case(case: dict[str, Any], corpus: list[dict[str, Any]], top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    embed = get_embedding_provider().embed
    query_vec = embed(case["question"])
    ranked = sorted(corpus, key=lambda c: _cosine(query_vec, c["embedding"]), reverse=True)
    top = ranked[:top_k]

    expected_docs = set(case.get("expected_documents", []))
    retrieved_docs = {c["document_name"] for c in top}
    recall = bool(expected_docs & retrieved_docs)

    keywords = [k.lower() for k in case.get("expected_keywords", [])]
    haystack = " ".join(c["content"].lower() for c in top)
    grounded = sum(1 for k in keywords if k in haystack)
    grounding = grounded / len(keywords) if keywords else 0.0

    min_citations = int(case.get("minimum_expected_citation_count", 1))
    citation_ok = len(top) >= min_citations

    passed = recall and grounding >= 0.5 and citation_ok
    return {
        "question": case["question"],
        "expected_documents": sorted(expected_docs),
        "retrieved_documents": sorted(retrieved_docs),
        "recall_at_k": recall,
        "keyword_grounding": round(grounding, 4),
        "citation_ok": citation_ok,
        "passed": passed,
    }


def evaluate(top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    corpus = build_corpus()
    cases = load_eval_cases()
    results = [score_case(case, corpus, top_k) for case in cases]
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    recall_hits = sum(1 for r in results if r["recall_at_k"])
    grounding_avg = sum(r["keyword_grounding"] for r in results) / total if total else 0.0
    return {
        "cases": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "recall_at_k": round(recall_hits / total, 4) if total else 0.0,
        "grounding_rate": round(grounding_avg, 4),
        "top_k": top_k,
        "corpus_chunks": len(corpus),
        "results": results,
    }
