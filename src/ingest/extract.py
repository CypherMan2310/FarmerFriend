"""Extract per-page text from the source manifest (PDF via pypdf, HTML via trafilatura)."""

from __future__ import annotations

import argparse
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterator

import trafilatura
from pypdf import PdfReader

from src.config import load_config, repo_path

log = logging.getLogger(__name__)

# Unicode letter ranges of the expected script per language.
_SCRIPT_RANGES: dict[str, tuple[int, int]] = {
    "ta": (0x0B80, 0x0BFF),
    "hi": (0x0900, 0x097F),
}
MIN_SCRIPT_RATIO = 0.6
MIN_TEXT_CHARS = 50


def clean_text(text: str) -> str:
    """Normalise to NFC, collapse space runs, and keep paragraph breaks."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace(" ", " ").replace("\x00", "")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def script_ratio(text: str, language: str) -> float:
    """Share of letters in ``text`` that belong to the script expected for ``language``.

    Tamil: U+0B80-U+0BFF, Hindi: U+0900-U+097F, English: ASCII letters. Returns 0.0 when
    the text has no letters.
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    if language in _SCRIPT_RANGES:
        lo, hi = _SCRIPT_RANGES[language]
        hits = sum(1 for c in letters if lo <= ord(c) <= hi)
    else:
        hits = sum(1 for c in letters if c.isascii())
    return hits / len(letters)


def is_text_ok(text: str, ratio: float) -> bool:
    """True when the page has enough text and enough of it is in the expected script."""
    return ratio >= MIN_SCRIPT_RATIO and len(text) >= MIN_TEXT_CHARS


def extract_pdf_pages(path: Path) -> list[str]:
    """Return the raw text of each page of a PDF (one string per page)."""
    reader = PdfReader(path)
    return [page.extract_text() or "" for page in reader.pages]


def extract_html_text(html: str, url: str | None = None) -> str:
    """Return the main text of an HTML string using trafilatura ('' if none found)."""
    return trafilatura.extract(html, url=url, include_tables=True, include_comments=False) or ""


def extract_document(entry: dict[str, Any], root: Path | None = None) -> list[dict[str, Any]]:
    """Extract one manifest entry into per-page records.

    Args:
        entry: Manifest object (id, title, url, language, format, file).
        root: Directory that ``entry["file"]`` is relative to; defaults to the repo root.

    Returns:
        One record per page with script_ratio and text_ok set.
    """
    base = root if root is not None else repo_path(".")
    path = base / entry["file"]
    if entry["format"] == "pdf":
        raw_pages = extract_pdf_pages(path)
    elif entry["format"] == "html":
        html = path.read_text(encoding="utf-8", errors="replace")
        raw_pages = [extract_html_text(html, entry.get("url"))]
    else:
        raise ValueError(f"unsupported format {entry['format']!r} for {entry['id']}")
    lang = entry["language"]
    records = []
    for i, raw in enumerate(raw_pages, start=1):
        text = clean_text(raw)
        ratio = round(script_ratio(text, lang), 4)
        records.append(
            {
                "doc_id": entry["id"],
                "title": entry.get("title", ""),
                "url": entry.get("url", ""),
                "language": lang,
                "page": i,
                "text": text,
                "text_en": text if lang == "en" else None,
                "script_ratio": ratio,
                "text_ok": is_text_ok(text, ratio),
            }
        )
    return records


def read_manifest(path: Path) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from a JSONL manifest, skipping blank lines."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def run(only: list[str] | None = None, root: Path | None = None) -> dict[str, tuple[int, int]]:
    """Extract every manifest document and write config paths.extracted.

    Args:
        only: Restrict to these document ids (None = all).
        root: Base directory for manifest-relative files; defaults to the repo root.

    Returns:
        Mapping doc_id -> (pages, pages with text_ok).
    """
    cfg = load_config()
    manifest = repo_path(cfg["paths"]["source_manifest"])
    out_path = repo_path(cfg["paths"]["extracted"])
    base = root if root is not None else repo_path(".")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary: dict[str, tuple[int, int]] = {}
    with out_path.open("w", encoding="utf-8", newline="\n") as out:
        for entry in read_manifest(manifest):
            if only and entry["id"] not in only:
                continue
            if not (base / entry["file"]).is_file():
                log.warning("missing file for %s: %s", entry["id"], entry["file"])
                continue
            recs = extract_document(entry, base)
            for rec in recs:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            summary[entry["id"]] = (len(recs), sum(r["text_ok"] for r in recs))
    return summary


def main(argv: list[str] | None = None) -> None:
    """CLI entry point: ``python -m src.ingest.extract [--only ID ...]``."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="+", help="document ids to extract")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run(args.only)
    for doc_id, (pages, ok) in summary.items():
        print(f"{doc_id}: {pages} pages, {ok} ok")
    print(
        f"{len(summary)} docs, {sum(p for p, _ in summary.values())} pages, "
        f"{sum(o for _, o in summary.values())} ok"
    )


if __name__ == "__main__":
    main()
