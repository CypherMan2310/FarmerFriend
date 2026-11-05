"""Translate between Tamil/Hindi and English.

Backends are tried in config order (models.translation.backend_order): IndicTrans2 (gated on
Hugging Face) first, then NLLB-200. The chosen one is exposed as ``Translator.backend``.
"""

from __future__ import annotations

import re
from typing import Any

import torch

from src.config import load_config
from src.translate.glossary import missing_figures

_SENT = re.compile(r"(?<=[.!?।])\s+|\n+")
_MAX_SEG_CHARS = 400


def split_segments(text: str) -> list[str]:
    """Split text into sentence-sized segments short enough for the translator."""
    out: list[str] = []
    for s in (x.strip() for x in _SENT.split(text)):
        while len(s) > _MAX_SEG_CHARS:
            cut = max(s.rfind(", ", 0, _MAX_SEG_CHARS), s.rfind("; ", 0, _MAX_SEG_CHARS))
            cut = cut + 1 if cut > 0 else _MAX_SEG_CHARS
            out.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            out.append(s)
    return out


class Translator:
    """Batch translator for ``ta``/``hi`` <-> ``en`` using the first backend that loads."""

    def __init__(self, cfg: dict[str, Any] | None = None, device: str | None = None) -> None:
        self.cfg = cfg or load_config()
        self.t = self.cfg["models"]["translation"]
        self.codes: dict[str, str] = self.cfg["languages"]["indictrans_codes"]
        self.device = device or (self.t["device"] if torch.cuda.is_available() else "cpu")
        self.dtype = getattr(torch, self.t["dtype"]) if self.device == "cuda" else torch.float32
        self._models: dict[str, tuple[Any, Any]] = {}
        self.errors: dict[str, str] = {}
        self.backend: str | None = None
        for name in self.t["backend_order"]:
            try:
                getattr(self, f"_init_{name}")()
                self.backend = name
                break
            except Exception as exc:  # gated repo, missing files, OOM
                self.errors[name] = f"{type(exc).__name__}: {exc}"[:300]
        if self.backend is None:
            raise RuntimeError(f"No translation backend could be loaded: {self.errors}")

    def _load(self, name: str, remote_code: bool) -> tuple[Any, Any]:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(name, trust_remote_code=remote_code)
        model = AutoModelForSeq2SeqLM.from_pretrained(
            name, trust_remote_code=remote_code, torch_dtype=self.dtype
        )
        return tok, model.to(self.device).eval()

    def _init_indictrans2(self) -> None:
        from src.translate._vendor.indic_processor import IndicProcessor

        self._models["indic_en"] = self._load(self.t["indic_en"], True)
        self._models["en_indic"] = self._load(self.t["en_indic"], True)
        self._ip = IndicProcessor(inference=True)

    def _init_nllb(self) -> None:
        self._models["nllb"] = self._load(self.t["nllb"], False)

    @torch.no_grad()
    def _generate(self, batch: list[str], src: str, tgt: str) -> list[str]:
        gen = {"num_beams": self.t["num_beams"], "max_length": self.t["max_length"]}
        if self.backend == "indictrans2":
            tok, model = self._models["indic_en" if tgt == "eng_Latn" else "en_indic"]
            pre = self._ip.preprocess_batch(batch, src_lang=src, tgt_lang=tgt)
            enc = tok(pre, truncation=True, padding="longest", return_tensors="pt").to(self.device)
            out = tok.batch_decode(model.generate(**enc, **gen), skip_special_tokens=True,
                                   clean_up_tokenization_spaces=True)
            return self._ip.postprocess_batch(out, lang=tgt)
        tok, model = self._models["nllb"]
        tok.src_lang = src
        enc = tok(batch, truncation=True, padding=True, max_length=self.t["max_length"],
                  return_tensors="pt").to(self.device)
        out = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(tgt), **gen)
        return tok.batch_decode(out, skip_special_tokens=True)

    def translate(self, texts: list[str], src: str, tgt: str) -> list[str]:
        """Translate short texts (sentences) from ``src`` to ``tgt`` (``ta``/``hi``/``en``)."""
        if src == tgt or not texts:
            return list(texts)
        s, t, bs = self.codes[src], self.codes[tgt], self.t["batch_size"]
        out: list[str] = []
        for i in range(0, len(texts), bs):
            out.extend(self._generate(texts[i:i + bs], s, t))
        return [o.strip() for o in out]

    def translate_long(self, text: str, src: str, tgt: str) -> str:
        """Translate a paragraph or page by splitting it into segments."""
        segs = split_segments(text)
        return " ".join(self.translate(segs, src, tgt)) if segs else ""

    def translate_answer(self, text_en: str, tgt: str) -> str:
        """Translate an English answer sentence by sentence; keep figures exact.

        If a translated sentence loses any number from the English sentence, the English
        sentence is kept in brackets after it, so no dose or figure is altered.
        """
        if tgt == "en":
            return text_en
        segs = split_segments(text_en)
        outs = self.translate(segs, "en", tgt)
        return " ".join(o if not missing_figures(s, o) else f"{o} ({s})" for s, o in zip(segs, outs))
