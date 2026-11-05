"""Groundedness judge.

LLM judge: the answer model is asked, per claim, whether its cited source states it
(yes/no). A lexical check (word overlap >= 0.5 and every figure present in the source)
runs alongside. No external API is used; a stronger judge model would be more reliable,
and the same-model bias is reported in eval/report.md.
"""

from __future__ import annotations

import re
from typing import Any

from src.translate.glossary import figures

_WORD = re.compile(r"[a-z]{3,}")
JUDGE_PROMPT = ("<context> {source} <user> Does the context above state the following claim? "
                "Reply with only yes or no. Claim: {claim} <assistant>")


def lexical_support(claim: str, source: str) -> bool:
    """Word overlap >= 0.5 and every figure in the claim appears in the source."""
    cw = set(_WORD.findall(claim.lower()))
    if not cw:
        return False
    overlap = len(cw & set(_WORD.findall(source.lower()))) / len(cw)
    return overlap >= 0.5 and set(figures(claim)) <= set(figures(source))


def llm_support(llm: Any, claim: str, source: str) -> bool:
    """Ask the LLM judge whether ``source`` states ``claim``."""
    src = source[:1500]
    reply = llm.generate(JUDGE_PROMPT.format(source=src, claim=claim), max_new_tokens=3)
    return reply.strip().lower().startswith("yes")


def judge_sentences(llm: Any | None, sentences: list[dict[str, Any]],
                    sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Judge each ``{"text", "cite"}`` sentence against its cited source."""
    out = []
    for s in sentences:
        src = sources[s["cite"] - 1]["text"] if 1 <= s["cite"] <= len(sources) else ""
        lex = lexical_support(s["text"], src)
        llm_ok = llm_support(llm, s["text"], src) if llm is not None else lex
        out.append({**s, "lexical": lex, "llm": llm_ok, "supported": lex and llm_ok})
    return out
