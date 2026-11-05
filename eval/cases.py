"""Evaluation case template and loader for eval/cases.jsonl.

One JSON object per line:
{
  "id": "c01",
  "category": "crop" | "irrigation" | "fertilizer" | "clarify" | "refuse",
  "lang": "ta" | "hi" | "en",
  "question": "...",                 # in ``lang``
  "expected_action": "answer" | "clarify" | "refuse",
  "gold_facts": ["...", "..."],      # 2-4 key facts copied from the source (answer cases)
  "gold_doc": "icar01",              # source document id (answer cases)
  "evidence": "exact phrase"         # substring of the supporting chunk, used for hit@5
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATEGORIES = {"crop", "irrigation", "fertilizer", "clarify", "refuse"}
ACTIONS = {"answer", "clarify", "refuse"}
TEMPLATE = {"id": "c00", "category": "crop", "lang": "en", "question": "",
            "expected_action": "answer", "gold_facts": [], "gold_doc": "", "evidence": ""}


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load and validate cases; raises ValueError on a malformed case."""
    cases = [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
    ids = set()
    for c in cases:
        missing = set(TEMPLATE) - set(c)
        if missing:
            raise ValueError(f"{c.get('id')}: missing {sorted(missing)}")
        if c["category"] not in CATEGORIES or c["expected_action"] not in ACTIONS:
            raise ValueError(f"{c['id']}: bad category/action")
        if c["lang"] not in {"ta", "hi", "en"}:
            raise ValueError(f"{c['id']}: bad lang")
        if c["expected_action"] == "answer" and not (2 <= len(c["gold_facts"]) <= 4 and c["gold_doc"]):
            raise ValueError(f"{c['id']}: answer cases need 2-4 gold facts and a gold_doc")
        if c["id"] in ids:
            raise ValueError(f"duplicate id {c['id']}")
        ids.add(c["id"])
    return cases
