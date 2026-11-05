"""Sentence embeddings with the configured multilingual model (bge-m3, fallback e5)."""

from __future__ import annotations

from typing import Any

import numpy as np

from src.config import load_config


class Embedder:
    """Normalised embeddings from the first configured embedding model that loads."""

    def __init__(self, device: str = "cpu", cfg: dict[str, Any] | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        cfg = cfg or load_config()
        e = cfg["models"]["embedding"]
        self.batch_size = cfg["retrieval"]["embed_batch_size"]
        errors = {}
        for name in [e["primary"], *e.get("fallbacks", [])]:
            try:
                self.model = SentenceTransformer(name, device=device)
                self.name = name
                break
            except Exception as exc:
                errors[name] = f"{type(exc).__name__}: {exc}"[:200]
        else:
            raise RuntimeError(f"No embedding model loaded: {errors}")
        if device == "cuda":
            self.model.half()

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return an (n, dim) float32 array of L2-normalised embeddings."""
        vecs = self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=len(texts) > 200)
        return vecs.astype(np.float32)
