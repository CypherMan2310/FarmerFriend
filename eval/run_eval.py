"""Run the 40 evaluation cases end to end and write eval/results.jsonl + eval/metrics.md.

Usage: python eval/run_eval.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cases import load_cases  # noqa: E402
from judge import judge_sentences  # noqa: E402
from metrics import (chrf, factual_correctness, qa_correct, retrieval_hit,  # noqa: E402
                     right_language, summarise)

from src.agent.pipeline import Assistant  # noqa: E402
from src.config import load_config, repo_path  # noqa: E402
from src.translate.glossary import english_terms, figures  # noqa: E402

_SENT = re.compile(r"(?<=[.!?])\s+")
_CITE = re.compile(r"\[(\d+)\]")
_WORD = re.compile(r"[a-z]{3,}")


def parse_cited(answer_en: str) -> list[dict]:
    """Split a final English answer 'sentence [n] sentence [m]' into {"text", "cite"}."""
    parts = re.findall(r"(.+?)\s*\[(\d+)\]", answer_en)
    return [{"text": t.strip(), "cite": int(n)} for t, n in parts]


def raw_sentences(raw: str, sources: list[dict]) -> list[dict]:
    """Raw LLM sentences with their own citation or the best-overlap source."""
    out = []
    for s in (x.strip() for x in _SENT.split(raw)):
        bare = _CITE.sub("", s).strip()
        if not bare or "NO_SOURCE" in bare or not sources:
            continue
        cites = [int(n) for n in _CITE.findall(s) if 1 <= int(n) <= len(sources)]
        if not cites:
            w = set(_WORD.findall(bare.lower()))
            cites = [1 + max(range(len(sources)), key=lambda i: len(
                w & set(_WORD.findall(sources[i]["text"].lower()))))]
        out.append({"text": bare, "cite": cites[0]})
    return out


def tag_failure(case: dict, row: dict) -> str | None:
    """One cause per failed case, in priority order."""
    if row["action"] != case["expected_action"]:
        return "wrong router action"
    if not row["lang_ok"]:
        return "translation error"
    if case["expected_action"] != "answer":
        return None
    if not row["hit"]:
        return "translation error" if row["lost_terms"] else "retrieval miss"
    if any(not s["supported"] for s in row["judged"]):
        return "hallucination"
    if row["factual"] < 0.5:
        gold = set(figures(" ".join(case["gold_facts"])))
        ans = set(figures(row["answer_en"]))
        if gold and ans and not gold <= ans:
            return "unit or dosage error"
        return "other"
    return None


def main() -> None:
    """Evaluate every case and write results and metrics."""
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config()
    cases = load_cases(repo_path(cfg["paths"]["eval_cases"]))
    bot = Assistant(cfg)
    rows, back_h, back_r = [], [], []
    for c in cases:
        res = bot.ask(c["question"], c["lang"])
        row = {k: res[k] for k in ("lang", "query_en", "action", "reason", "answer", "answer_en",
                                   "no_source", "raw_llm", "latency_s")}
        row.update(id=c["id"], category=c["category"], expected_action=c["expected_action"],
                   question=c["question"], lang_ok=right_language(res["answer"], c["lang"]),
                   retrieved=[s["chunk_id"] for s in res["retrieved"]])
        row["mode"] = res.get("mode")
        row["hit"] = bool(c["gold_doc"]) and retrieval_hit(res["retrieved"], c["gold_doc"], c["evidence"])
        row["judged"] = judge_sentences(bot.llm, parse_cited(res["answer_en"]), res["sources"]) \
            if res["action"] == "answer" and not res["no_source"] else []
        row["raw_judged"] = judge_sentences(bot.llm, raw_sentences(res["raw_llm"], res["sources"]),
                                            res["sources"]) if res["raw_llm"] else []
        row["factual"] = factual_correctness(c["gold_facts"], res["answer_en"]) \
            if c["expected_action"] == "answer" else None
        row["qa_correct"] = qa_correct(c, res, row["factual"] or 0.0)
        lost = []
        if c["lang"] != "en":
            plain = bot.translator.translate([c["question"]], c["lang"], "en")[0]
            back_h.append(bot.translator.translate([plain], "en", c["lang"])[0])
            back_r.append(c["question"])
            lost = [t for t in english_terms(c["question"], c["lang"])
                    if not any(w in plain.lower() for w in t.split())]
        row["lost_terms"] = lost
        row["failure"] = tag_failure(c, row)
        rows.append(row)
        print(f"{c['id']} {c['lang']} exp={c['expected_action']} got={res['action']}"
              f"{' (no source)' if res['no_source'] else ''} hit={row['hit']} "
              f"fact={row['factual']} {res['latency_s']}s fail={row['failure']}", flush=True)

    summary = summarise(rows)
    summary["back_translation_chrF"] = round(chrf(back_h, back_r), 1)
    summary["translator_backend"] = bot.translator.backend
    summary["llm"] = bot.llm.name
    with repo_path("eval/results.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    counts: dict[str, int] = {}
    for r in rows:
        if r["failure"]:
            counts[r["failure"]] = counts.get(r["failure"], 0) + 1
    lines = ["# Evaluation metrics (auto-generated by eval/run_eval.py)", "",
             "| metric | value |", "| --- | --- |"]
    lines += [f"| {k} | {v} |" for k, v in summary.items()]
    lines += ["", "## Failure tags", "", "| cause | cases |", "| --- | --- |"]
    lines += [f"| {k} | {v} |" for k, v in sorted(counts.items(), key=lambda x: -x[1])]
    lines += ["", "## Per case", "",
              "| id | cat | lang | expected | got | hit@5 | facts | grounded | QA | s | failure |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        g = (f"{sum(s['supported'] for s in r['judged'])}/{len(r['judged'])}"
             if r["judged"] else "-")
        got = r["action"] + (" (no source)" if r["no_source"] else "")
        f = "-" if r["factual"] is None else f"{r['factual']:.2f}"
        lines.append(f"| {r['id']} | {r['category']} | {r['lang']} | {r['expected_action']} | "
                     f"{got} | {'yes' if r['hit'] else 'no'} | {f} | {g} | "
                     f"{int(r['qa_correct'])} | {r['latency_s']} | {r['failure'] or ''} |")
    repo_path("eval/metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
