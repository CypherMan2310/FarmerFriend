"""Tests for BM25 tokenisation, RRF fusion and (if the index exists) hybrid search."""

import pytest

from src.config import load_config, repo_path
from src.retrieval.hybrid import rrf_merge, tokenize


def test_tokenize_drops_stopwords_keeps_numbers() -> None:
    assert tokenize("How much N for the wheat crop, 120 kg/ha?") == ["much", "n", "wheat", "crop", "120", "kg", "ha"]


def test_rrf_prefers_items_ranked_high_in_both_lists() -> None:
    scores = rrf_merge([["a", "b", "c"], ["b", "a", "d"]], rrf_k=60)
    assert max(scores, key=scores.get) in {"a", "b"}
    assert scores["b"] > scores["c"] and scores["a"] > scores["d"]


def test_hybrid_search_returns_top_k() -> None:
    cfg = load_config()
    if not (repo_path(cfg["paths"]["index_dir"]) / "chroma").exists():
        pytest.skip("index not built")
    from src.retrieval.hybrid import HybridRetriever

    hits = HybridRetriever(cfg).search("drip irrigation benefits")
    assert len(hits) == cfg["retrieval"]["top_k"]
    assert all({"chunk_id", "doc_id", "text", "score", "dense_sim"} <= h.keys() for h in hits)
    assert any("drip" in h["text"].lower() for h in hits)
