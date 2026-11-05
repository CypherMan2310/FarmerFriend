"""Render data/SOURCES.md from the manifest data/sources.jsonl (the source of truth)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config, repo_path  # noqa: E402

HEADER = """# Sources

Generated from `data/sources.jsonl` by `scripts/render_sources.py`. Accessed 2026-11-05.
Every URL returned HTTP 200 when checked. Licence class:
`open` (CC or equivalent), `permitted_with_attribution` (publisher allows reuse with
acknowledgement), `restricted` (all rights reserved / prior permission), `unclear` (no
statement found).

**Use in this project.** This is a non-commercial academic prototype. All documents are used
locally for retrieval, and every answer cites its source. Raw files (`data/raw/`) and chunk
text (`data/chunks.jsonl`) are not committed, because most sources are `restricted` or
`unclear`; `scripts/download_sources.py` and the ingest scripts rebuild them. Restricted
sources would need the publisher's permission before any public deployment (ICAR's policy
offers free permission on request).

| id | title | publisher | lang | licence | licence source | URL |
| --- | --- | --- | --- | --- | --- | --- |
"""


def main() -> None:
    """Write SOURCES.md."""
    cfg = load_config()
    rows = [json.loads(x) for x in repo_path(cfg["paths"]["source_manifest"]).read_text(encoding="utf-8").splitlines() if x.strip()]
    lines = [
        f"| {r['id']} | {r['title']} | {r['publisher']} | {r['language']} | {r['licence_class']} "
        f"| [policy]({r['licence_url']}) | [link]({r['url']}) |"
        for r in rows
    ]
    repo_path(cfg["paths"]["sources"]).write_text(HEADER + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} sources")


if __name__ == "__main__":
    main()
