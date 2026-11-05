"""Phase 0 model check: load each configured checkpoint on this machine and get one output.

Usage:
    python scripts/model_check.py --only llm|translation|embedding [--model HF_ID]

Each run appends one JSON line per check to logs/model_check.jsonl and prints a short
summary. docs/MODEL_CHECK.md is written from those results.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config, repo_path  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
LOG = repo_path("logs/model_check.jsonl")

# Neutral test inputs: no doses or figures (CLAUDE.md rule 2).
LLM_CONTEXT = (
    "Drip irrigation delivers water directly to the root zone of plants through emitters, "
    "which reduces evaporation and runoff losses compared with flood irrigation."
)
LLM_QUESTION = "According to the context, what is one benefit of drip irrigation? Answer in one sentence."
INDIC_SAMPLES = {
    "hin_Deva": "गेहूं की फसल में सिंचाई कब करनी चाहिए?",
    "tam_Taml": "நெல் பயிருக்கு எப்போது நீர் பாய்ச்ச வேண்டும்?",
}
EN_SAMPLE = "When should I irrigate my wheat crop?"


def _reset_peak() -> None:
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()


def _peak_vram_gb() -> float | None:
    return round(torch.cuda.max_memory_allocated() / 1e9, 2) if DEVICE == "cuda" else None


def check_llm(model_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    """Load a ParamBharatGen-family causal LM and answer one context-based question."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    llm_cfg = cfg["models"]["llm"]
    dtype = getattr(torch, llm_cfg["dtype"]) if DEVICE == "cuda" else torch.float32
    t0 = time.perf_counter()
    # Model card loads the tokenizer without remote code and the model with it.
    tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, trust_remote_code=llm_cfg["trust_remote_code"], torch_dtype=dtype
    ).to(DEVICE)
    model.eval()
    load_s = time.perf_counter() - t0

    prompt = f"<context> {LLM_CONTEXT} <user> {LLM_QUESTION} <assistant>"
    inputs = tok(prompt, return_tensors="pt").to(DEVICE)
    result: dict[str, Any] = {"prompt_tokens": int(inputs["input_ids"].shape[1])}
    for use_cache in (True, False):
        try:
            t1 = time.perf_counter()
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=60,
                    do_sample=False,
                    eos_token_id=tok.eos_token_id,
                    pad_token_id=tok.pad_token_id or tok.eos_token_id,
                    use_cache=use_cache,
                )
            new_tokens = out[0][inputs["input_ids"].shape[1]:]
            result.update(
                use_cache=use_cache,
                gen_s=round(time.perf_counter() - t1, 2),
                new_tokens=int(new_tokens.shape[0]),
                output=tok.decode(new_tokens, skip_special_tokens=True).strip(),
            )
            break
        except Exception as exc:  # record and retry without KV cache
            result[f"error_use_cache_{use_cache}"] = f"{type(exc).__name__}: {exc}"[:300]
    result.update(load_s=round(load_s, 1), dtype=str(dtype))
    return result


def _translate(model_id: str, sentences: list[str], src: str, tgt: str) -> list[str]:
    from src.translate._vendor.indic_processor import IndicProcessor
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id, trust_remote_code=True).to(DEVICE)
    model.eval()
    ip = IndicProcessor(inference=True)
    batch = ip.preprocess_batch(sentences, src_lang=src, tgt_lang=tgt)
    enc = tok(batch, truncation=True, padding="longest", return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        gen = model.generate(**enc, max_length=256, num_beams=5, num_return_sequences=1)
    decoded = tok.batch_decode(gen, skip_special_tokens=True, clean_up_tokenization_spaces=True)
    return ip.postprocess_batch(decoded, lang=tgt)


def check_translation(cfg: dict[str, Any]) -> dict[str, Any]:
    """Translate the Indic samples to English and the English sample to Hindi and Tamil."""
    tcfg = cfg["models"]["translation"]
    out: dict[str, Any] = {}
    t0 = time.perf_counter()
    for src, text in INDIC_SAMPLES.items():
        out[f"{src}->eng_Latn"] = _translate(tcfg["indic_en"], [text], src, "eng_Latn")[0]
    for tgt in INDIC_SAMPLES:
        out[f"eng_Latn->{tgt}"] = _translate(tcfg["en_indic"], [EN_SAMPLE], "eng_Latn", tgt)[0]
    out["total_s"] = round(time.perf_counter() - t0, 1)
    return out


def check_embedding(model_id: str) -> dict[str, Any]:
    """Embed an English question, its Hindi version and an unrelated sentence; compare."""
    from sentence_transformers import SentenceTransformer

    t0 = time.perf_counter()
    model = SentenceTransformer(model_id, device=DEVICE)
    load_s = time.perf_counter() - t0
    texts = [EN_SAMPLE, INDIC_SAMPLES["hin_Deva"], "The stock market closed higher today."]
    emb = model.encode(texts, normalize_embeddings=True, convert_to_tensor=True)
    sims = (emb @ emb.T).tolist()
    return {
        "dim": int(emb.shape[1]),
        "load_s": round(load_s, 1),
        "cos(en_q, hi_q)": round(sims[0][1], 3),
        "cos(en_q, unrelated)": round(sims[0][2], 3),
        "cross_lingual_ok": sims[0][1] > sims[0][2],
    }


def main() -> None:
    """Run one check and log the result."""
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["llm", "translation", "embedding"], required=True)
    ap.add_argument("--model", help="Override checkpoint (e.g. a fallback from config.yaml)")
    args = ap.parse_args()
    cfg = load_config()

    model_id = args.model or {
        "llm": cfg["models"]["llm"]["primary"],
        "translation": cfg["models"]["translation"]["indic_en"],
        "embedding": cfg["models"]["embedding"]["primary"],
    }[args.only]
    record: dict[str, Any] = {
        "check": args.only,
        "model": model_id,
        "device": torch.cuda.get_device_name(0) if DEVICE == "cuda" else platform.processor(),
        "torch": torch.__version__,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    _reset_peak()
    try:
        if args.only == "llm":
            record.update(check_llm(model_id, cfg))
        elif args.only == "translation":
            record.update(check_translation(cfg))
        else:
            record.update(check_embedding(model_id))
        record["ok"] = True
    except Exception as exc:
        record.update(ok=False, error=f"{type(exc).__name__}: {exc}"[:500])
        traceback.print_exc(limit=3)
    record["peak_vram_gb"] = _peak_vram_gb()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
