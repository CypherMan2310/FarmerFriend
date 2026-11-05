# Farmer Advisory Assistant
Purpose: Tamil/Hindi/English crop, irrigation, fertilizer Q&A, grounded in curated documents.
Source of truth: BUILD_PLAN.md. If a request and BUILD_PLAN.md disagree, ask the user.

## Rules (strict)
1. Read TODO.md and WORK.md before starting. Update both after every task.
2. Never invent model names, checkpoints, URLs, library APIs or pesticide/fertilizer figures.
   Verify a checkpoint exists on Hugging Face and loads before use; if not, tell the user
   and use the fallback in config.yaml.
3. Answers come only from retrieved chunks. No supporting chunk -> say there is no source
   and suggest asking a local agriculture officer. Never guess.
4. Never show a dose, pesticide or fertilizer figure that is not in a cited chunk.
   Put the citation next to every such figure.
5. Model names, paths, top_k and languages live in config.yaml only. Nothing hard-coded in src/.
6. Touch only the files the task needs. No whole-repo rewrites. Never paste whole documents
   or long logs into the conversation.
7. One module per commit, with a short pytest test. Tick a TODO only after its test passes.
8. Type hints and docstrings on public functions. No secrets in the repo; keys via env vars.
9. Work phase by phase. End of phase: stop, summarise in 5 lines, wait for "go".
10. State which Claude model a task needs before starting it (routing below).

## Architecture
detect lang (Unicode script, no model) -> IndicTrans2 to English (+ glossary for crops/units)
-> router (answer | clarify | refuse) -> hybrid retrieve top 5 (dense + BM25, merged)
-> AgriParam grounded answer + chunk citations -> IndicTrans2 back to user language
-> Gradio UI: chat, language selector, sources panel, thumbs up/down log.
English is the pivot language; the index holds English chunks only.

## Stack
Python 3.12 (plan says 3.11; not installed here), transformers, IndicTrans2 (gated; NLLB-200
fallback in use), sentence-transformers, ChromaDB, rank_bm25, Gradio, pytest.
Hardware: RTX 4060 Laptop 8 GB VRAM, 40 GB RAM, Windows 11.

## Layout
config.yaml | data/{raw/, SOURCES.md, chunks.jsonl} | src/{ingest,translate,retrieval,agent,app}/
eval/{cases.jsonl, run_eval.py, metrics.py, judge.py, report.md} | docs/ | tests/

## Claude model routing
- Haiku 5.5, thinking off/minimal: move/copy/rename files, folders, tick TODO/WORK,
  run commands, format JSONL.
- Sonnet 5.5, thinking low-medium: README/docs, SOURCES.md, test cases, glue code,
  Gradio layout, ingestion + chunking, reading code/logs to find a bug.
- Opus 5.5, thinking high: hybrid retriever, grounded prompt, router/agent, eval harness
  + judge, model-loading and translation-quality debugging. Medium: failure-analysis write-up.
