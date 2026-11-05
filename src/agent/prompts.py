"""Grounded prompt (AgriParam format) and the fixed messages for non-answer actions."""

from __future__ import annotations

from typing import Any, Callable

RULES = (
    "Answer the farmer's question using ONLY the numbered sources in the context. "
    "Put the source number like [1] after every sentence. Copy every number, dose and unit "
    "exactly as written in the source. If the sources do not answer the question, reply "
    "only: NO_SOURCE. Answer in at most 5 short sentences."
)

NO_SOURCE = ("I could not find this in my source documents, so I cannot answer it reliably. "
             "Please ask your local agriculture officer or Krishi Vigyan Kendra.")
REFUSE_DOMAIN = ("I can only answer questions about crops, irrigation and fertilizers, "
                 "based on agricultural advisory documents.")
REFUSE_DOSE = ("I cannot give a pesticide or chemical dose that is not written in my source "
               "documents. Please ask your local agriculture officer before spraying.")
CLARIFY = ("Which crop is this for? If you can, also tell me your district or state and the "
           "season (kharif or rabi).")


def build_prompt(question: str, chunks: list[dict[str, Any]], count: Callable[[str], int],
                 budget: int) -> tuple[str, list[dict[str, Any]]]:
    """Build ``<context> [n] ... <user> rules + question <assistant>`` within ``budget`` tokens.

    Lowest-ranked chunks are dropped until the prompt fits. Returns (prompt, chunks used).
    """
    used = list(chunks)
    while True:
        ctx = " ".join(f"[{i}] {c['text']}" for i, c in enumerate(used, 1))
        prompt = f"<context> {ctx} <user> {RULES} Question: {question} <assistant>"
        if count(prompt) <= budget or len(used) <= 1:
            return prompt, used
        used.pop()
