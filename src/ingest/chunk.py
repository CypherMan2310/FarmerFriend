"""Chunk English page text into overlapping, token-capped chunks (across pages per document)."""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Iterable

from src.config import load_config, repo_path

CountTokens = Callable[[str], int]

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def make_token_counter(model_name: str | None = None) -> CountTokens:
    """Build a token counter from the answer LLM tokenizer (config models.llm.primary)."""
    from transformers import AutoTokenizer

    name = model_name or load_config()["models"]["llm"]["primary"]
    tok = AutoTokenizer.from_pretrained(name, trust_remote_code=False)
    return lambda text: len(tok(text, add_special_tokens=False)["input_ids"])


def split_sentences(text: str) -> list[str]:
    """Split text into sentences/paragraph lines, dropping empties."""
    return [s.strip() for s in _SENT_SPLIT.split(text) if s and s.strip()]


def split_long(sentence: str, max_tokens: int, count: CountTokens) -> list[str]:
    """Split one over-long sentence on word boundaries into pieces of <= max_tokens."""
    pieces: list[str] = []
    cur: list[str] = []
    for word in sentence.split():
        if cur and count(" ".join(cur + [word])) > max_tokens:
            pieces.append(" ".join(cur))
            cur = []
        cur.append(word)
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def _join(items: list[tuple[str, int]]) -> str:
    return " ".join(s for s, _ in items)


def chunk_units(
    units: list[tuple[str, int]],
    max_tokens: int,
    overlap_tokens: int,
    min_tokens: int,
    count: CountTokens,
) -> list[dict[str, Any]]:
    """Greedily pack (sentence, page) units into chunks.

    Returns dicts with text, page, page_end, n_tokens. Each chunk is <= max_tokens,
    including the sentences carried over as overlap from the previous chunk.
    """
    prepared: list[tuple[str, int]] = []
    for sent, page in units:
        if count(sent) > max_tokens:
            prepared.extend((p, page) for p in split_long(sent, max_tokens, count))
        else:
            prepared.append((sent, page))

    chunks: list[list[tuple[str, int]]] = []
    cur: list[tuple[str, int]] = []
    fresh = 0  # units in cur that are new (not overlap carried from the previous chunk)
    for unit in prepared:
        if cur and count(_join(cur + [unit])) > max_tokens:
            if fresh:
                chunks.append(cur)
            carry: list[tuple[str, int]] = []
            for u in reversed(cur):
                if count(_join([u] + carry)) > overlap_tokens:
                    break
                carry.insert(0, u)
            while carry and count(_join(carry + [unit])) > max_tokens:
                carry.pop(0)
            cur, fresh = carry, 0
        cur.append(unit)
        fresh += 1
    if cur and fresh:
        chunks.append(cur)

    def build(items: list[tuple[str, int]]) -> dict[str, Any]:
        text = _join(items)
        return {"text": text, "page": items[0][1], "page_end": items[-1][1], "n_tokens": count(text)}

    out = [build(c) for c in chunks]
    if len(out) > 1 and out[-1]["n_tokens"] < min_tokens:
        merged_text = out[-2]["text"] + " " + out[-1]["text"]
        n = count(merged_text)
        if n <= max_tokens:
            out[-2] = {
                "text": merged_text,
                "page": out[-2]["page"],
                "page_end": out[-1]["page_end"],
                "n_tokens": n,
            }
            out.pop()
    return out


def chunk_document(
    pages: list[dict[str, Any]],
    count: CountTokens,
    max_tokens: int,
    overlap_tokens: int,
    min_tokens: int,
) -> list[dict[str, Any]]:
    """Chunk one document's extracted page records (already filtered to usable pages)."""
    ordered = sorted(pages, key=lambda r: r["page"])
    units: list[tuple[str, int]] = []
    for rec in ordered:
        units.extend((s, rec["page"]) for s in split_sentences(rec["text_en"]))
    if not units:
        return []
    raw = chunk_units(units, max_tokens, overlap_tokens, min_tokens, count)
    first = ordered[0]
    return [
        {
            "chunk_id": f"{first['doc_id']}-{n:04d}",
            "doc_id": first["doc_id"],
            "title": first["title"],
            "url": first["url"],
            "language": first["language"],
            **c,
        }
        for n, c in enumerate(raw, start=1)
    ]


def chunk_records(
    records: Iterable[dict[str, Any]],
    count: CountTokens,
    max_tokens: int,
    overlap_tokens: int,
    min_tokens: int,
) -> tuple[list[dict[str, Any]], int]:
    """Chunk page records grouped by doc_id.

    Returns:
        (chunks, skipped_pages) where skipped pages have text_ok false or no text_en.
    """
    by_doc: dict[str, list[dict[str, Any]]] = {}
    skipped = 0
    for rec in records:
        if not rec.get("text_ok") or not rec.get("text_en"):
            skipped += 1
            continue
        by_doc.setdefault(rec["doc_id"], []).append(rec)
    chunks: list[dict[str, Any]] = []
    for pages in by_doc.values():
        chunks.extend(chunk_document(pages, count, max_tokens, overlap_tokens, min_tokens))
    return chunks, skipped


def run(count: CountTokens | None = None) -> dict[str, Any]:
    """Read paths.extracted, write paths.chunks, and return summary statistics."""
    cfg = load_config()
    ch = cfg["chunking"]
    counter = count or make_token_counter()
    src = repo_path(cfg["paths"]["extracted"])
    with src.open(encoding="utf-8") as fh:
        records = [json.loads(line) for line in fh if line.strip()]
    chunks, skipped = chunk_records(
        records, counter, ch["max_tokens"], ch["overlap_tokens"], ch["min_tokens"]
    )
    dst = repo_path(cfg["paths"]["chunks"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8", newline="\n") as out:
        for c in chunks:
            out.write(json.dumps(c, ensure_ascii=False) + "\n")
    toks = [c["n_tokens"] for c in chunks]
    return {
        "docs": len({c["doc_id"] for c in chunks}),
        "chunks": len(chunks),
        "mean_tokens": sum(toks) / len(toks) if toks else 0.0,
        "max_tokens": max(toks, default=0),
        "skipped_pages": skipped,
    }


def main() -> None:
    """CLI entry point: ``python -m src.ingest.chunk``."""
    s = run()
    print(
        f"docs={s['docs']} chunks={s['chunks']} mean_tokens={s['mean_tokens']:.1f} "
        f"max_tokens={s['max_tokens']} skipped_pages={s['skipped_pages']}"
    )


if __name__ == "__main__":
    main()
