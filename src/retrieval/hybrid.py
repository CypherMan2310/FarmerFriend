"""Hybrid retrieval: dense (English + original-language query) and BM25, merged with RRF."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from src.config import load_config
from src.retrieval.index import load_chunks, open_collection

_WORD = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")
_STOP = set("a an the of in on for to and or is are be by with at as what how when which "
            "should i my me do does can per from it this that".split())


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens without stopwords, for BM25."""
    return [w for w in _WORD.findall(text.lower()) if w not in _STOP]


def rrf_merge(rankings: list[list[str]], rrf_k: int) -> dict[str, float]:
    """Reciprocal-rank fusion of several ranked id lists."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
    return scores


class HybridRetriever:
    """Top-k chunks for a query using Chroma (dense) and BM25, fused with RRF."""

    def __init__(self, cfg: dict[str, Any] | None = None, embedder: Any = None) -> None:
        from src.retrieval.embed import Embedder

        self.cfg = cfg or load_config()
        r = self.cfg["retrieval"]
        self.k, self.cand, self.rrf_k = r["top_k"], r["candidate_k"], r["rrf_k"]
        self.chunks = load_chunks(self.cfg)
        self.by_id = {c["chunk_id"]: c for c in self.chunks}
        self.ids = [c["chunk_id"] for c in self.chunks]
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in self.chunks])
        self.col = open_collection(self.cfg)
        self.embedder = embedder or Embedder(device=r["query_device"], cfg=self.cfg)

    def _dense(self, query: str) -> tuple[list[str], dict[str, float]]:
        vec = self.embedder.encode([query])[0].tolist()
        res = self.col.query(query_embeddings=[vec], n_results=self.cand)
        ids = res["ids"][0]
        return ids, {i: 1.0 - d for i, d in zip(ids, res["distances"][0])}

    def _bm25(self, query: str) -> list[str]:
        scores = self.bm25.get_scores(tokenize(query))
        top = np.argsort(scores)[::-1][: self.cand]
        return [self.ids[i] for i in top if scores[i] > 0]

    def search(self, query_en: str, query_native: str | None = None,
               k: int | None = None) -> list[dict[str, Any]]:
        """Return the top-k chunks with ``score`` (RRF) and ``dense_sim`` (best cosine)."""
        rankings, sims = [], {}
        ids, s = self._dense(query_en)
        rankings.append(ids)
        sims.update(s)
        if query_native and query_native != query_en:
            ids, s = self._dense(query_native)
            rankings.append(ids)
            for i, v in s.items():
                sims[i] = max(v, sims.get(i, -1.0))
        rankings.append(self._bm25(query_en))
        fused = rrf_merge(rankings, self.rrf_k)
        top = sorted(fused, key=fused.get, reverse=True)[: k or self.k]
        return [{**self.by_id[i], "score": round(fused[i], 5),
                 "dense_sim": round(sims.get(i, 0.0), 4)} for i in top]
