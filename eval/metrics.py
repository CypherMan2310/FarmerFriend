"""Per-case and aggregate metrics for the evaluation (see BUILD_PLAN.md section 5)."""

from __future__ import annotations

import re
import statistics
from typing import Any

from src.translate.glossary import figures
from src.translate.langdetect import detect_language

_WORD = re.compile(r"[a-z]{3,}")
_STOP = set("the and for with that this are from per should apply which when what".split())


def retrieval_hit(sources: list[dict[str, Any]], gold_doc: str, evidence: str) -> bool:
    """Gold chunk in top 5: a retrieved chunk from the gold doc containing the evidence phrase."""
    ev = evidence.lower()
    return any(s["doc_id"] == gold_doc and ev in s["text"].lower() for s in sources)


def fact_present(fact: str, answer_en: str) -> bool:
    """A gold fact counts as present if all its figures and >= 50% of its words appear."""
    a = answer_en.lower()
    words = {w for w in _WORD.findall(fact.lower()) if w not in _STOP}
    if not set(figures(fact)) <= set(figures(answer_en)):
        return False
    return not words or len([w for w in words if w in a]) / len(words) >= 0.5


def factual_correctness(gold_facts: list[str], answer_en: str) -> float:
    """Share of gold key facts present in the English answer."""
    return sum(fact_present(f, answer_en) for f in gold_facts) / len(gold_facts) if gold_facts else 0.0


def right_language(answer: str, lang: str) -> bool:
    """Answer is in the user's language (script check)."""
    return detect_language(answer) == lang


def qa_correct(case: dict[str, Any], res: dict[str, Any], factual: float) -> bool:
    """Domain QA accuracy (0/1): correct action, right language and, for answers, >= half the facts."""
    if res["action"] != case["expected_action"] or not right_language(res["answer"], case["lang"]):
        return False
    return case["expected_action"] != "answer" or (not res["no_source"] and factual >= 0.5)


def chrf(hyps: list[str], refs: list[str]) -> float:
    """Corpus chrF (sacrebleu)."""
    from sacrebleu.metrics import CHRF

    return CHRF().corpus_score(hyps, [refs]).score if hyps else 0.0


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate metrics over per-case rows produced by run_eval."""
    ans = [r for r in rows if r["expected_action"] == "answer"]
    judged = [s for r in ans for s in r["judged"]]
    raw = [s for r in ans for s in r["raw_judged"]]
    mean = lambda xs: round(sum(xs) / len(xs), 3) if xs else 0.0  # noqa: E731
    return {
        "cases": len(rows),
        "retrieval_hit@5": mean([r["hit"] for r in ans]),
        "groundedness_final": mean([s["supported"] for s in judged]),
        "groundedness_raw_llm": mean([s["supported"] for s in raw]),
        "factual_correctness": mean([r["factual"] for r in ans]),
        "domain_qa_accuracy": mean([r["qa_correct"] for r in rows]),
        "router_accuracy": mean([r["action"] == r["expected_action"] for r in rows]),
        "no_source_rate_answer_cases": mean([r["no_source"] for r in ans]),
        "median_latency_s": round(statistics.median(r["latency_s"] for r in rows), 2),
    }
