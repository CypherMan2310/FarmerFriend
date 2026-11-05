"""Offline tests for extraction and chunking (whitespace token counter)."""

from src.ingest.chunk import chunk_records
from src.ingest.extract import extract_document, extract_html_text, is_text_ok, script_ratio


def wc(text: str) -> int:
    """Whitespace token counter."""
    return len(text.split())


def sentence(i: int, n: int = 10) -> str:
    return " ".join(f"w{i}x{j}" for j in range(n)) + "."


def page(doc: str, p: int, text: str, ok: bool = True) -> dict:
    return {"doc_id": doc, "title": "T", "url": "http://u", "language": "en",
            "page": p, "text": text, "text_en": text, "script_ratio": 1.0, "text_ok": ok}


def make(n_sent: int, per_page: int = 10) -> list[dict]:
    recs = []
    for p in range(0, n_sent, per_page):
        text = " ".join(sentence(i) for i in range(p, min(p + per_page, n_sent)))
        recs.append(page("d1", p // per_page + 1, text))
    return recs


def test_cap_overlap_metadata():
    chunks, skipped = chunk_records(make(40), wc, 50, 12, 20)
    assert skipped == 0 and len(chunks) > 2
    assert all(c["n_tokens"] <= 50 for c in chunks)
    for a, b in zip(chunks, chunks[1:]):
        assert a["text"].split()[-1] in b["text"].split()  # trailing sentence carried over
    keys = {"chunk_id", "doc_id", "title", "url", "language", "page", "page_end", "n_tokens", "text"}
    assert all(keys <= set(c) for c in chunks)
    assert chunks[0]["chunk_id"] == "d1-0001"
    assert chunks[-1]["page_end"] == 4  # chunks span pages


def test_short_tail_merged_only_when_fits():
    text = " ".join(sentence(i) for i in range(5))  # 5 sentences x 10 words
    chunks, _ = chunk_records([page("d", 1, text)], wc, 45, 0, 20)
    assert len(chunks) == 2  # tail of 10 < 20 but merged result (50) > 45: kept
    chunks, _ = chunk_records([page("d", 1, text)], wc, 50, 0, 20)
    assert len(chunks) == 1 and chunks[0]["n_tokens"] == 50
    # a tail below min_tokens whose merge would exceed the cap is kept as its own chunk
    # (greedy packing means a merge that fits only happens when the cap allows it).
    chunks, _ = chunk_records([page("d", 1, text)], wc, 45, 0, 5)
    assert len(chunks) == 2 and chunks[-1]["n_tokens"] == 10


def test_long_sentence_split_and_skips():
    long = " ".join(f"a{i}" for i in range(130)) + "."
    recs = [page("d", 1, long), page("d", 2, "ignored text here.", ok=False)]
    recs.append({**page("d", 3, "x"), "text_en": None})
    chunks, skipped = chunk_records(recs, wc, 50, 5, 10)
    assert skipped == 2
    assert len(chunks) >= 3 and all(c["n_tokens"] <= 50 for c in chunks)


def test_script_ratio():
    garbage = "Fkpvcd hpjkd lkjhg asdf qwerty zxcvb poiuy mnbvc lkjhg fdsa qazwsx edcrfv tgbyhn"
    tamil = ("நெல் சாகுபடிக்கு "
             "போதுமான நீர் பாசனம் "
             "மிகவும் அவசியம் "
             "ஆகும் என்று விவசாயிகள்")
    r_bad, r_ok = script_ratio(garbage, "ta"), script_ratio(tamil, "ta")
    assert r_bad < 0.6 and not is_text_ok(garbage, r_bad)
    assert r_ok >= 0.6 and is_text_ok(tamil, r_ok)
    assert script_ratio("Rice needs water", "en") == 1.0


def test_html_extraction_and_document(tmp_path):
    body = " ".join(
        f"Paddy fields need steady irrigation during tillering stage number {i}." for i in range(8)
    )
    html = f"<html><body><article><h1>Rice</h1><p>{body}</p></article></body></html>"
    assert "irrigation" in extract_html_text(html)
    (tmp_path / "a.html").write_text(html, encoding="utf-8")
    entry = {"id": "a", "title": "A", "url": "http://x", "language": "en",
             "format": "html", "file": "a.html"}
    recs = extract_document(entry, tmp_path)
    assert len(recs) == 1 and recs[0]["page"] == 1 and recs[0]["text_ok"]
    assert recs[0]["text_en"] == recs[0]["text"]
