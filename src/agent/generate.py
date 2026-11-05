"""Answer LLM (AgriParam, fallback Param-1) and grounding checks on its output.

AgriParam's custom code uses legacy tuple KV caches, which break inside
transformers' ``generate()``; ``LLM.generate`` therefore runs its own greedy loop with
tuple caches and falls back to ``generate(use_cache=False)`` if that fails.
"""

from __future__ import annotations

import re
from typing import Any, Callable

import torch

from src.config import load_config
from src.translate.glossary import figures

_SENT = re.compile(r"(?<=[.!?])\s+")
_CITE = re.compile(r"\[(\d+)\]")
_WORD = re.compile(r"[a-z]{3,}")
_STOP = set("the and for with that this are was were from have has into per can should "
            "will also about which when what your their them they then than been".split())


class LLM:
    """Causal LM wrapper with greedy decoding and a token budget."""

    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.cfg = cfg or load_config()
        m = self.cfg["models"]["llm"]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = getattr(torch, m["dtype"]) if self.device == "cuda" else torch.float32
        errors = {}
        for name in [m["primary"], *m.get("fallbacks", [])]:
            try:
                self.tok = AutoTokenizer.from_pretrained(name, trust_remote_code=False)
                self.model = AutoModelForCausalLM.from_pretrained(
                    name, trust_remote_code=m["trust_remote_code"], torch_dtype=dtype
                ).to(self.device).eval()
                self.name = name
                break
            except Exception as exc:
                errors[name] = f"{type(exc).__name__}: {exc}"[:200]
        else:
            raise RuntimeError(f"No answer LLM loaded: {errors}")
        self.max_ctx, self.max_new = m["max_context_tokens"], m["max_new_tokens"]

    def count(self, text: str) -> int:
        """Number of tokens in ``text``."""
        return len(self.tok(text, add_special_tokens=False)["input_ids"])

    @torch.no_grad()
    def generate(self, prompt: str, max_new_tokens: int | None = None) -> str:
        """Greedy-decode a completion for ``prompt`` (truncated to fit the context window)."""
        n_new = max_new_tokens or self.max_new
        ids = self.tok(prompt, return_tensors="pt")["input_ids"][:, -(self.max_ctx - n_new):]
        ids = ids.to(self.device)
        try:
            out = self._greedy_cached(ids, n_new)
        except Exception:
            out = self.model.generate(ids, max_new_tokens=n_new, do_sample=False, use_cache=False,
                                      eos_token_id=self.tok.eos_token_id,
                                      pad_token_id=self.tok.eos_token_id)[0, ids.shape[1]:].tolist()
        return self.tok.decode(out, skip_special_tokens=True).strip()

    def _greedy_cached(self, ids: torch.Tensor, n_new: int) -> list[int]:
        mask = torch.ones_like(ids)
        res = self.model(input_ids=ids, attention_mask=mask, use_cache=True)
        past, out = res.past_key_values, []
        for _ in range(n_new):
            tok_id = self._pick(res.logits[0, -1, :], out)
            nxt = torch.tensor([[tok_id]], device=ids.device)
            if tok_id == self.tok.eos_token_id:
                break
            out.append(tok_id)
            mask = torch.cat([mask, torch.ones_like(nxt)], dim=1)
            res = self.model(input_ids=nxt, attention_mask=mask, past_key_values=past, use_cache=True)
            past = res.past_key_values
        return out

    @staticmethod
    def _pick(logits: torch.Tensor, out: list[int], n: int = 3) -> int:
        """Greedy choice that never repeats an n-gram already generated."""
        banned = {tuple(out[i:i + n]) for i in range(len(out) - n + 1)}
        for cand in torch.topk(logits, 10).indices.tolist():
            if len(out) < n - 1 or tuple(out[-(n - 1):] + [cand]) not in banned:
                return cand
        return int(logits.argmax())


def _content_words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


def _source_sentences(chunks: list[dict[str, Any]]) -> list[tuple[int, str]]:
    """(1-based chunk index, sentence) for every sentence of the chunks."""
    return [(i, s.strip()) for i, c in enumerate(chunks, 1) for s in _SENT.split(c["text"])
            if len(s.strip()) > 20]


def is_statement(sentence: str, min_words: int = 6) -> bool:
    """True for a sentence that can serve as an answer: not a question, not a short heading.

    Source documents contain FAQ-style question headings; quoting one ("What is the best
    method ...?") would answer every similar question with the same non-answer.
    """
    s = sentence.strip()
    return not s.endswith("?") and len(s.split()) >= min_words


def extractive_answer(question: str, chunks: list[dict[str, Any]],
                      embed: Callable[[list[str]], Any], crops: set[str], k: int = 2,
                      min_sim: float = 0.45, max_chars: int = 600) -> list[dict[str, Any]]:
    """Quote the ``k`` source sentences most similar to the question (verbatim, cited).

    If the question names a crop, only chunks mentioning that crop are used, so a figure is
    never quoted from a passage about another crop. Sentences are ranked by embedding
    cosine similarity and returned in document order.
    """
    q = question.lower()
    asked = {c for c in crops if re.search(rf"\b{c}", q)}
    usable = [(i, c) for i, c in enumerate(chunks, 1)
              if not asked or any(a in c["text"].lower() for a in asked)]
    cands = [(i, s.strip()) for i, c in usable for s in _SENT.split(c["text"])
             if 30 <= len(s.strip()) <= max_chars and is_statement(s)]
    if not cands:
        return []
    vecs = embed([question] + [s for _, s in cands])
    sims = (vecs[1:] @ vecs[0]).tolist()
    picked: list[int] = []
    for j in sorted(range(len(cands)), key=lambda j: -sims[j]):
        if len(picked) == k or sims[j] < min_sim:
            break
        if cands[j][1] not in {cands[p][1] for p in picked}:  # chunk overlap repeats text
            picked.append(j)
    picked.sort()
    return [{"text": cands[j][1], "cite": cands[j][0], "sim": round(sims[j], 3)} for j in picked]


def ground_answer(answer: str, chunks: list[dict[str, Any]],
                  min_overlap: float = 0.5) -> list[dict[str, Any]]:
    """Keep only answer sentences supported by a single source sentence.

    A generated sentence is kept if one sentence of a retrieved chunk contains every figure
    it states and shares at least ``min_overlap`` of its content words; it is cited to that
    chunk. Everything else is dropped, so no figure is shown out of its source context.

    Returns:
        List of ``{"text", "cite"}`` with ``cite`` a 1-based chunk index.
    """
    src = [(i, _content_words(s), set(figures(s))) for i, s in _source_sentences(chunks)]
    kept: list[dict[str, Any]] = []
    for sent in (s.strip() for s in _SENT.split(answer)):
        bare = _CITE.sub("", sent).strip()
        cw = _content_words(bare)
        if not bare or "NO_SOURCE" in bare or not cw or not src or not is_statement(bare, 3):
            continue
        figs = set(figures(bare))
        best = max(src, key=lambda x: (figs <= x[2], len(cw & x[1])))
        if figs <= best[2] and len(cw & best[1]) / len(cw) >= min_overlap                 and bare not in {k["text"] for k in kept}:
            kept.append({"text": bare, "cite": best[0]})
    return kept
