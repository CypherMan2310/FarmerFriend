# Model check (Phase 0)

Date: 2026-11-05. Goal: confirm each checkpoint in `config.yaml` exists on Hugging Face,
loads on this machine and produces output. Reproduce with
`python scripts/model_check.py --only llm|translation|embedding`; raw results are appended
to `logs/model_check.jsonl` (not committed).

## Hardware and software

| Item | Value |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4060 Laptop, 8 GB VRAM, driver 610.78 |
| CPU / RAM | Intel i7-12650H / 40 GB |
| OS | Windows 11 |
| Python | 3.12 (plan says 3.11, which is not installed here) |
| torch | 2.15.0+cu132 |
| transformers | pinned `<5`: AgriParam and IndicTrans2 ship custom code written for 4.x |

## 1. Checkpoints exist (Hugging Face API, 2026-11-05)

| Role | Checkpoint | Exists | Gated | Licence | Weights on disk | Params |
| --- | --- | --- | --- | --- | --- | --- |
| Answer LLM | `bharatgenai/AgriParam` | yes | no | apache-2.0 | 11.4 GB (stored fp32) | 2.86 B |
| LLM fallback | `bharatgenai/Param-1-2.9B-Instruct` | yes | no | apache-2.0 | 5.7 GB | 2.86 B |
| Indic to English | `ai4bharat/indictrans2-indic-en-dist-200M` | yes | yes (auto-approve) | MIT | 1.8 GB | 228 M |
| English to Indic | `ai4bharat/indictrans2-en-indic-dist-200M` | yes | yes (auto-approve) | MIT | 2.2 GB | 275 M |
| Translation fallback | `ai4bharat/indictrans2-{indic-en,en-indic}-1B` | yes | yes | MIT | not downloaded | 1 B |
| Embeddings | `BAAI/bge-m3` | yes | no | MIT | 2.3 GB | 568 M |
| Embedding fallback | `intfloat/multilingual-e5-base` | yes | no | MIT | not downloaded | 278 M |

Notes from the model cards and configs:
- AgriParam is a fine-tune of Param-1-2.9B-Instruct (architecture `ParamBharatGenForCausalLM`,
  needs `trust_remote_code=True`). Prompt format from its card:
  `<context> ... <user> ... <assistant>`. Training data: English plus a Hindi translation.
- **AgriParam context window is 2048 tokens** (`max_position_embeddings`). Top 5 chunks of
  300-500 tokens (1500-2500 tokens) plus the prompt and up to 300 new tokens does not fit.
  Needs a decision before Phase 4 (see "Open issues").
- IndicTrans2 repos are gated: an unauthenticated request returns 401. Downloads need a
  Hugging Face token whose account has accepted the model terms.

## 2. Loads and produces output on this machine

All runs on the RTX 4060 Laptop GPU, torch 2.15.0+cu132, transformers 4.57.6.

| Model | Loaded | dtype | Load time | Peak VRAM | Output |
| --- | --- | --- | --- | --- | --- |
| `bharatgenai/AgriParam` | yes | bfloat16 | 10.7 s | 5.85 GB | see below |
| `BAAI/bge-m3` | yes | float32 | 16.4 s | 2.28 GB | 1024-dim vectors, cross-lingual check passed |
| IndicTrans2 dist-200M (both) | **deferred** | | | | download refused: 403, token cannot read gated repos |

**AgriParam** (greedy, context-based prompt `<context> ... <user> ... <assistant>`, 48 prompt
tokens, 15 new tokens in 1.25 s):
> Context: drip irrigation delivers water to the root zone, reducing evaporation and runoff.
> Q: According to the context, what is one benefit of drip irrigation?
> A: "Drip irrigation reduces evaporation and runoff losses compared to flood irrigation."

Generation **with the KV cache fails** inside the model's custom code
(`AttributeError: 'NoneType' object has no attribute 'shape'`); it works with
`use_cache=False`, which is also what the model card uses. Without a cache each new token
re-reads the whole prompt, so a 2000-token prompt with 300 new tokens will be slow.

**bge-m3**: cosine("When should I irrigate my wheat crop?", same question in Hindi) = 0.772;
cosine(English question, unrelated sentence about the stock market) = 0.286.

**IndicTrans2**: deferred by user decision on 2026-11-05. The terms were accepted, but the
cached token is a fine-grained token with no permissions, so both downloads still return
403 `GatedRepoError`. Fix before Phase 2: give the token "Read access to contents of all
public gated repos you can access" (or log in with a Read token via `hf auth login`), then
run `python scripts/download_models.py --only translation` and
`python scripts/model_check.py --only translation`.
The vendored `IndicProcessor` passes an offline test (`tests/test_vendor_indic_processor.py`).
Non-gated alternative checked but not adopted: `facebook/nllb-200-distilled-600M` (covers
Tamil and Hindi, licence CC-BY-NC-4.0).

## 3. Decisions and fallbacks

- **IndicTransToolkit**: v1.1.1 (only PyPI release) is Cython-only with no Windows wheel, and
  building it needs Microsoft C++ Build Tools, which are not installed. The pure-Python
  `IndicProcessor` from v1.0.2 (MIT, commit `0c607654e8`) is vendored in
  `src/translate/_vendor/` instead. Same public API; v1.0.3+ changes are a Cython speed-up,
  a fix for multiple generations per sentence (not used here) and collator/evaluator refactors.
  To be diffed against 1.1.1 in Phase 2.

## Open issues

1. AgriParam's 2048-token window versus top-5 chunks of 300-500 tokens.
2. AgriParam KV cache crashes; `use_cache=False` makes long prompts slow (Phase 4 debugging).
3. VRAM: AgriParam 5.85 GB + bge-m3 2.28 GB (fp32) already exceed 8 GB before translation
   models. Plan for Phase 4/5: bge-m3 in fp16 or on CPU, IndicTrans2 on CPU or loaded on demand.
4. IndicTrans2 load check deferred until the Hugging Face token can read gated repos
   (user action, before Phase 2).
