"""Command-line assistant.

Usage:
    python -m src.agent.cli "question" [--lang ta|hi|en]
    python -m src.agent.cli --file eval/cli_queries.jsonl --out eval/cli_run.md
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.config import repo_path


def format_result(r: dict[str, Any]) -> str:
    """Markdown block for one answered question."""
    lines = [f"**Q ({r['lang']}):** {r['question']}", f"- English query: {r['query_en']}",
             f"- Action: `{r['action']}` ({r['reason']}){' - no source' if r['no_source'] else ''}",
             f"- Answer: {r['answer']}"]
    if r["lang"] != "en":
        lines.append(f"- Answer (English): {r['answer_en']}")
    for s in r["sources"]:
        if s["cited"]:
            lines.append(f"- [{s['n']}] {s['title']} (doc {s['doc_id']}, p. {s['page']}) {s['url']}")
    lines.append(f"- Latency: {r['latency_s']} s")
    return "\n".join(lines)


def main() -> None:
    """Answer one question or a JSONL file of {"question", "lang"?} records."""
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--lang", choices=["ta", "hi", "en"])
    ap.add_argument("--file")
    ap.add_argument("--out")
    args = ap.parse_args()
    from src.agent.pipeline import Assistant

    bot = Assistant()
    items = ([json.loads(x) for x in repo_path(args.file).read_text(encoding="utf-8").splitlines()
              if x.strip()] if args.file else [{"question": args.question, "lang": args.lang}])
    blocks = []
    for it in items:
        block = format_result(bot.ask(it["question"], it.get("lang")))
        print(block + "\n", flush=True)
        blocks.append(block)
    if args.out:
        repo_path(args.out).write_text("# CLI run\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
