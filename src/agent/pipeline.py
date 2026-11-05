"""End-to-end assistant: detect -> translate -> route -> retrieve -> generate -> translate back."""

from __future__ import annotations

import time
from typing import Any

from src.agent import prompts
from src.agent.generate import LLM, ground_answer
from src.agent.query import prepare_query
from src.agent.router import route
from src.config import load_config


class Assistant:
    """Holds the translator, retriever and LLM; ``ask`` answers one question."""

    def __init__(self, cfg: dict[str, Any] | None = None, load_llm: bool = True) -> None:
        from src.retrieval.hybrid import HybridRetriever
        from src.translate.indictrans import Translator

        self.cfg = cfg or load_config()
        self.translator = Translator(self.cfg)
        self.retriever = HybridRetriever(self.cfg)
        self.llm = LLM(self.cfg) if load_llm else None
        self._msg_cache: dict[tuple[str, str], str] = {}

    def _msg(self, text: str, lang: str) -> str:
        key = (text, lang)
        if key not in self._msg_cache:
            self._msg_cache[key] = self.translator.translate_answer(text, lang)
        return self._msg_cache[key]

    def ask(self, question: str, lang: str | None = None) -> dict[str, Any]:
        """Answer a question. ``lang`` forces the language (else detected from script).

        Returns a dict with lang, query_en, action, reason, answer (user language),
        answer_en, no_source, sources (chunks shown, with ``cited`` flags) and latency_s.
        """
        t0 = time.perf_counter()
        pq = prepare_query(question, self.translator, lang)
        retrieved = self.retriever.search(pq.english, pq.native)
        decision = route(pq.english, pq.native, pq.lang, retrieved, self.cfg)
        out: dict[str, Any] = {"lang": pq.lang, "question": question, "query_en": pq.english,
                               "action": decision.action, "reason": decision.reason,
                               "no_source": False, "sources": [], "raw_llm": "",
                               "retrieved": retrieved}
        if decision.action == "refuse":
            msg = prompts.REFUSE_DOSE if "dose" in decision.reason else prompts.REFUSE_DOMAIN
            out.update(answer_en=msg, answer=self._msg(msg, pq.lang))
        elif decision.action == "clarify":
            out.update(answer_en=prompts.CLARIFY, answer=self._msg(prompts.CLARIFY, pq.lang))
        else:
            self._answer(pq, retrieved, out)
        out["latency_s"] = round(time.perf_counter() - t0, 2)
        return out

    def _answer(self, pq: Any, retrieved: list[dict[str, Any]], out: dict[str, Any]) -> None:
        kept: list[dict[str, Any]] = []
        used = retrieved
        best_sim = max((c["dense_sim"] for c in retrieved), default=0.0)
        if self.llm is not None and best_sim >= self.cfg["router"]["answer_min_sim"]:
            budget = self.llm.max_ctx - self.llm.max_new
            prompt, used = prompts.build_prompt(pq.english, retrieved, self.llm.count, budget)
            out["raw_llm"] = self.llm.generate(prompt)
            kept = ground_answer(out["raw_llm"], used)
        cited = {s["cite"] for s in kept}
        out["sources"] = [{**c, "n": i, "cited": i in cited} for i, c in enumerate(used, 1)]
        if not kept:
            out.update(no_source=True, answer_en=prompts.NO_SOURCE,
                       answer=self._msg(prompts.NO_SOURCE, pq.lang))
            return
        out["answer_en"] = " ".join(f"{s['text']} [{s['cite']}]" for s in kept)
        out["answer"] = " ".join(
            f"{self.translator.translate_answer(s['text'], pq.lang)} [{s['cite']}]" for s in kept)
