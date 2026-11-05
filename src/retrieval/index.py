"""Build the Chroma dense index from data/chunks.jsonl (BM25 is built in memory at load)."""

from __future__ import annotations

import json
from typing import Any

from src.config import load_config, repo_path


def load_chunks(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Read all chunk records."""
    cfg = cfg or load_config()
    path = repo_path(cfg["paths"]["chunks"])
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def open_collection(cfg: dict[str, Any] | None = None, reset: bool = False) -> Any:
    """Open (or recreate) the persistent Chroma collection."""
    import chromadb
    from chromadb.config import Settings

    cfg = cfg or load_config()
    client = chromadb.PersistentClient(path=str(repo_path(cfg["paths"]["index_dir"]) / "chroma"),
                                       settings=Settings(anonymized_telemetry=False))
    name = cfg["retrieval"]["collection"]
    if reset:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    return client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})


def build() -> int:
    """Embed every chunk on the index device and store it in Chroma. Returns chunk count."""
    from src.retrieval.embed import Embedder

    cfg = load_config()
    chunks = load_chunks(cfg)
    emb = Embedder(device=cfg["retrieval"]["index_device"], cfg=cfg)
    vecs = emb.encode([c["text"] for c in chunks])
    col = open_collection(cfg, reset=True)
    keys = ("doc_id", "title", "url", "language", "page", "page_end")
    for i in range(0, len(chunks), 500):
        part = chunks[i:i + 500]
        col.add(ids=[c["chunk_id"] for c in part], embeddings=vecs[i:i + 500].tolist(),
                documents=[c["text"] for c in part],
                metadatas=[{k: c[k] for k in keys} for c in part])
    return col.count()


if __name__ == "__main__":
    print(f"indexed {build()} chunks")
