"""Answer LLM (AgriParam, fallback Param-1) and grounding checks on its output.

AgriParam's custom code uses legacy tuple KV caches, which break inside
transformers' ``generate()``; ``LLM.generate`` therefore runs its own greedy loop with
tuple caches and falls back to ``generate(use_cache=False)`` if that fails.
"""

from __future__ import annotations

import re
from typing import Any

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
            nxt = res.logits[:, -1, :].argmax(-1, keepdim=True)
            tok_id = int(nxt)
            if tok_id == self.tok.eos_token_id:
                break
            out.append(tok_id)
            mask = torch.cat([mask, torch.ones_like(nxt)], dim=1)
            res = self.model(input_ids=nxt, attention_mask=mask, past_key_values=past, use_cache=True)
            past = res.past_key_values
        return out


def _content_words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


def ground_answer(answer: str, chunks: list[dict[str, Any]],
                  min_overlap: float = 0.35) -> list[dict[str, Any]]:
    """Keep only answer sentences supported by a retrieved chunk.

    Each kept sentence gets a citation (its own ``[n]`` if valid, else the chunk with the
    highest word overlap). A sentence is dropped if its word overlap with the cited chunk is
    below ``min_overlap`` or if any of its figures is not in that chunk.

    Returns:
        List of ``{"text", "cite"}`` with ``cite`` a 1-based chunk index.
    """
    kept = []
    words = [_content_words(c["text"]) for c in chunks]
    figs = [set(figures(c["text"])) for c in chunks]
    for sent in (s.strip() for s in _SENT.split(answer)):
        bare = _CITE.sub("", sent).strip()
        cw = _content_words(bare)
        if not bare or "NO_SOURCE" in bare or not cw:
            continue
        cited = [int(n) for n in _CITE.findall(sent) if 1 <= int(n) <= len(chunks)]
        overlaps = [len(cw & w) / len(cw) for w in words]
        best = cited[0] - 1 if cited and overlaps[cited[0] - 1] >= min_overlap else \
            max(range(len(chunks)), key=overlaps.__getitem__)
        if overlaps[best] < min_overlap:
            continue
        if any(f not in figs[best] for f in figures(bare)):
            continue  # a figure not present in the cited source is never shown
        kept.append({"text": bare, "cite": best + 1})
    return kept
