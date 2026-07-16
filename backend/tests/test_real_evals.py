"""Regression tests locking the eval to REAL retrieval behavior.

The previous /evals/run ignored the shipped eval datasets and scored 2
hardcoded questions against a mock LLM that always emitted citations, so it
always passed. These tests exercise the real corpus-based retrieval eval and
prove it discriminates (a fabricated query must fail).
"""
from __future__ import annotations

from app.evals.runner import build_corpus, evaluate, load_eval_cases, score_case


def test_shipped_eval_dataset_is_loaded():
    cases = load_eval_cases()
    # research (1) + annual-report (2) shipped cases
    assert len(cases) >= 3
    assert all("expected_documents" in c for c in cases)


def test_evaluate_computes_real_metrics():
    report = evaluate()
    assert report["corpus_chunks"] > 0
    assert report["cases"] >= 3
    assert 0.0 <= report["recall_at_k"] <= 1.0
    assert 0.0 <= report["grounding_rate"] <= 1.0


def test_retrieval_recalls_relevant_document():
    corpus = build_corpus()
    positive = {
        "question": "gpu inference privacy governance risk",
        "expected_documents": ["company-annual-report-ai-risk.md"],
        "expected_keywords": ["gpu", "inference", "privacy", "governance"],
        "minimum_expected_citation_count": 1,
    }
    result = score_case(positive, corpus)
    assert result["recall_at_k"] is True
    assert result["passed"] is True


def test_eval_discriminates_fabricated_query():
    # A nonsense query for a nonexistent document must NOT pass — proving the
    # eval is real and not a tautology.
    corpus = build_corpus()
    fabricated = {
        "question": "zzzq quantum banana xylophone nonexistent",
        "expected_documents": ["does-not-exist.md"],
        "expected_keywords": ["zzzq", "banana"],
        "minimum_expected_citation_count": 1,
    }
    result = score_case(fabricated, corpus)
    assert result["recall_at_k"] is False
    assert result["keyword_grounding"] == 0.0
    assert result["passed"] is False
