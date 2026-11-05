"""Phase 3: hit@5 of the hybrid retriever on 15 hand-labelled queries (en/hi/ta).

A query is a hit if any top-5 chunk comes from a gold document and contains a gold term.
Writes eval/retrieval_report.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agent.query import prepare_query  # noqa: E402
from src.config import repo_path  # noqa: E402
from src.retrieval.hybrid import HybridRetriever  # noqa: E402
from src.translate.indictrans import Translator  # noqa: E402


def is_hit(chunks: list[dict], gold_docs: list[str], gold_terms: list[str]) -> bool:
    """True if a chunk from a gold doc contains any gold term."""
    return any(c["doc_id"] in gold_docs and any(t in c["text"].lower() for t in gold_terms)
               for c in chunks)


def main() -> None:
    """Run all queries and write the report."""
    sys.stdout.reconfigure(encoding="utf-8")
    queries = [json.loads(x) for x in repo_path("eval/retrieval_queries.jsonl")
               .read_text(encoding="utf-8").splitlines() if x.strip()]
    tr, ret = Translator(), HybridRetriever()
    rows, hits, by_lang = [], 0, {}
    for q in queries:
        pq = prepare_query(q["query"], tr, q["lang"])
        top = ret.search(pq.english, pq.native)
        hit = is_hit(top, q["gold_docs"], q["gold_terms"])
        hits += hit
        by_lang.setdefault(q["lang"], []).append(hit)
        rows.append(f"| {q['id']} | {q['lang']} | {q['query']} | {pq.english} | "
                    f"{', '.join(q['gold_docs'])} | {', '.join(c['doc_id'] for c in top)} | "
                    f"{'yes' if hit else 'no'} |")
    lang_s = ", ".join(f"{k} {sum(v)}/{len(v)}" for k, v in by_lang.items())
    report = (
        "# Retrieval evaluation (Phase 3)\n\n"
        f"Hybrid retriever (bge-m3 dense on English + original query, BM25, RRF), translator "
        f"backend `{tr.backend}`. Hit = a top-5 chunk from a gold document containing a gold "
        f"term. Labels were set by hand from the source documents.\n\n"
        f"**hit@5 = {hits}/{len(queries)} = {hits / len(queries):.2f}** ({lang_s})\n\n"
        "| id | lang | query | English query used | gold docs | top-5 docs | hit |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n")
    repo_path("eval/retrieval_report.md").write_text(report, encoding="utf-8")
    print(f"hit@5 = {hits}/{len(queries)} ({lang_s})")


if __name__ == "__main__":
    main()
