"""Download the documents listed in data/sources.jsonl into data/raw/.

Usage:
    python scripts/download_sources.py [--only ID ...] [--force]

Raw documents are not committed (see .gitignore); this script rebuilds data/raw/ on a
fresh clone. Each manifest line needs: id, url, format ("pdf"|"html"), file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config, repo_path  # noqa: E402

USER_AGENT = "Mozilla/5.0 (compatible; FarmerAdvisoryAssistant/0.1; research use)"
TIMEOUT_S = 90


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Read the source manifest (one JSON object per line)."""
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fetch(url: str) -> tuple[bytes, str]:
    """GET a URL (following redirects) and return (body, content-type)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def looks_valid(body: bytes, fmt: str) -> bool:
    """Check the payload matches the declared format (guards against error pages)."""
    if fmt == "pdf":
        return body[:5] == b"%PDF-"
    return b"<html" in body[:4096].lower() or b"<!doctype html" in body[:4096].lower()


def main() -> None:
    """Download each manifest entry; report failures without stopping the others."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", help="Manifest ids to download")
    ap.add_argument("--force", action="store_true", help="Re-download existing files")
    args = ap.parse_args()
    cfg = load_config()
    entries = load_manifest(repo_path(cfg["paths"]["source_manifest"]))
    if args.only:
        entries = [e for e in entries if e["id"] in set(args.only)]

    failed: list[str] = []
    for e in entries:
        dest = repo_path(e["file"])
        if dest.exists() and not args.force:
            print(f"[skip] {e['id']} (exists)")
            continue
        try:
            body, ctype = fetch(e["url"])
            if not looks_valid(body, e["format"]):
                raise ValueError(f"payload is not {e['format']} (content-type {ctype!r})")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            sha = hashlib.sha256(body).hexdigest()[:16]
            print(f"[ok] {e['id']} {len(body) / 1e6:.2f} MB sha256:{sha}")
        except Exception as exc:  # network, HTTP error, wrong payload
            failed.append(e["id"])
            print(f"[fail] {e['id']}: {type(exc).__name__}: {str(exc)[:160]}")
        time.sleep(1)  # be polite to small institutional servers
    print(f"done: {len(entries) - len(failed)} ok/skipped, {len(failed)} failed {failed or ''}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
