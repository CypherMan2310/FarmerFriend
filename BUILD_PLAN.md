# Farmer Advisory Assistant: Build Plan

Put this file in the project root. Claude Code reads it as the source of truth for scope, architecture, phases, model routing and evaluation.

## 1. Scope and decisions

A chat app where a farmer asks a crop, irrigation or fertilizer question in Tamil, Hindi or English and gets a sourced answer in the same language. Every answer is grounded in a curated set of agricultural advisory documents, and the app shows the source passages beside it.

- **Languages:** Tamil, Hindi, English. Kannada is a stretch goal.
- **Domain:** crop selection and practices, irrigation scheduling, fertilizer and nutrient advice. Pest and disease questions only if a source document covers them.
- **Models:** BharatGen AgriParam as answer LLM, AI4Bharat IndicTrans2 for translation, a multilingual embedding model for retrieval. Verify AgriParam first (Phase 0). Fallback: Param1, then any open multilingual instruct model.
- **Agentic part:** a router that chooses between `answer`, `clarify` (ask for crop, district or season) and `refuse`.
- **Frontend:** Gradio, one page: chat, sources panel, language selector.
- **Out of scope:** voice, crop images, live weather or market prices, user accounts.
- **Rubric deliverables:** working app, 40 test cases with metrics, failure analysis, documentation, GitHub repository.

## 2. Architecture and stack

English is the pivot language: questions are translated in, answered from an English index, translated back out.

1. Detect language from Unicode script (Tamil, Devanagari, Latin). No model.
2. Translate to English with IndicTrans2, with a glossary so crop names and units (acre, kg/ha, NPK) survive.
3. Router returns `answer`, `clarify` or `refuse` (out of domain, or a pesticide dose with no source).
4. Retrieve top 5 chunks from the English index (dense embeddings + BM25, merged).
5. Generate a short answer from only those chunks, with chunk citations, using AgriParam.
6. Translate back to the user's language; show with source passages.

| Layer | Choice | Fallback |
| --- | --- | --- |
| Answer LLM | BharatGen AgriParam (Hugging Face) | Param1, then open multilingual instruct model |
| Translation | AI4Bharat IndicTrans2 distilled 200M | Full 1B models if GPU allows |
| Embeddings | BAAI/bge-m3 or multilingual-e5 | Any sentence-transformers model |
| Vector store | ChromaDB or FAISS, local | none |
| Keyword search | rank_bm25 | dense only |
| Frontend | Gradio | Streamlit |
| Compute | Free Colab/Kaggle GPU for models, laptop for the rest | CPU with small models |
| Language | Python 3.11 | |

Corpus: public agricultural advisory material (ICAR, state agricultural university package-of-practices documents, government crop guides). Collect 30 to 60 documents. Record URL and licence in `data/SOURCES.md` and confirm each licence allows this use before ingesting.

## 3. Phases (about two weeks, team of 3 to 4)

| Phase | Days | What gets built | Done when |
| --- | --- | --- | --- |
| 0. Setup and checks | 1 | Repo, CLAUDE.md/TODO.md/WORK.md, environment. Verify AgriParam, IndicTrans2, embedding checkpoints exist, load and fit the GPU. Record in `docs/MODEL_CHECK.md`. | One sentence from each model on this hardware |
| 1. Corpus | 2 | Collect 30-60 documents, log sources and licences, extract text, translate non-English text to English, chunk to 300-500 tokens with metadata | `data/chunks.jsonl` + `SOURCES.md` |
| 2. Translation layer | 1 | Script detection, IndicTrans2 wrapper, glossary, batch mode | 10 sample questions round-trip cleanly in ta and hi |
| 3. Retrieval | 2 | Embeddings, Chroma index, BM25, hybrid merge | Hit@5 measured on 15 hand-labelled queries |
| 4. Generation and router | 2 | Grounded prompt, citation format, router, no-source fallback | CLI answers 10 queries in 3 languages |
| 5. Frontend | 1 | Gradio chat, language selector, sources panel, feedback buttons | Runs on a fresh clone |
| 6. Evaluation | 3 | 40 test cases, metrics script, LLM judge plus manual check, failure analysis | `eval/report.md` with results table |
| 7. Polish | 2 | README, architecture diagram, demo video, cleanup, tag release | Rubric checklist all ticked |

**Risks and fallbacks**

- AgriParam will not load or is too large: switch to the fallback LLM in Phase 0, keep the rest unchanged. Model names come from `config.yaml`.
- Translation hurts retrieval: add the glossary, then test multilingual embeddings on the untranslated query as a second path.
- No GPU: use Colab for translation and generation and cache outputs so the frontend does not need them.

## 4. Model routing

Simple tasks go to Haiku, reading and writing tasks to Sonnet, complex building to Opus. Always the newest version (currently Haiku 5.5, Sonnet 5.5, Opus 5.5). Thinking effort is set per task.

| Task | Model | Thinking effort |
| --- | --- | --- |
| Rename, move, copy files; create folders; tick TODO.md/WORK.md | Haiku 5.5 | Off or minimal |
| Run commands, list source URLs, format JSONL | Haiku 5.5 | Minimal |
| README, docs, docstrings, SOURCES.md, test-case writing | Sonnet 5.5 | Low |
| Glue code: config loader, CLI, Gradio layout, unit tests | Sonnet 5.5 | Low to medium |
| Reading code or logs to find a bug | Sonnet 5.5 | Medium |
| Ingestion and chunking pipeline | Sonnet 5.5 | Medium |
| Hybrid retriever, grounded generation prompt, router/agent logic | Opus 5.5 | High |
| Evaluation harness, LLM judge, metric code | Opus 5.5 | High |
| Debugging model loading, GPU memory, translation quality | Opus 5.5 | High |
| Final failure analysis write-up | Opus 5.5 | Medium |

To save tokens: read only the files a task touches, keep `CLAUDE.md` short, never paste whole documents into the conversation.

## 5. Evaluation plan

40 cases (rubric asks for 30 to 50). Write the gold answers from the source documents by hand, not with an LLM.

| Category | Cases | Tamil | Hindi | English |
| --- | --- | --- | --- | --- |
| Crop practice | 10 | 4 | 4 | 2 |
| Irrigation | 8 | 3 | 3 | 2 |
| Fertilizer and nutrients | 8 | 3 | 3 | 2 |
| Needs clarification (no crop given) | 6 | 2 | 2 | 2 |
| Out of scope or unsafe (should refuse) | 8 | 3 | 3 | 2 |

Each case stores: id, language, question, expected action (`answer`, `clarify`, `refuse`), gold answer as 2 to 4 key facts, supporting source chunk.

**Metrics**

- Retrieval hit@5: gold chunk is in the top 5.
- Groundedness: share of answer claims supported by retrieved chunks. LLM judge, then check all 40 by hand.
- Factual correctness: share of gold key facts present in the answer.
- Domain QA accuracy: answer correct and in the right language, 0 or 1.
- Router accuracy: chosen action matches expected action.
- Translation sanity: back-translation chrF on the 30 non-English questions.
- Latency: median seconds per answer.

**Failure analysis.** Tag every failed case with one cause: translation error, retrieval miss, hallucination, unit or dosage error, wrong router action, other. Report counts and show two or three worked examples with the fix tried.

## 6. Repo structure

```text
farmer-advisory/
  CLAUDE.md          rules + architecture + stack (read first, keep short)
  TODO.md            work per module, ticked when done
  WORK.md            dated log of completed tasks
  BUILD_PLAN.md      this file
  README.md
  config.yaml        model names, paths, top_k, languages
  requirements.txt
  data/
    raw/             downloaded source documents
    SOURCES.md       URL + licence per document
    chunks.jsonl
  src/
    ingest/          extract.py, translate_docs.py, chunk.py
    translate/       indictrans.py, glossary.py, langdetect.py
    retrieval/       embed.py, index.py, hybrid.py
    agent/           router.py, prompts.py, generate.py
    app/             gradio_app.py
  eval/
    cases.jsonl      the 40 test cases
    run_eval.py, metrics.py, judge.py
    report.md        results + failure analysis
  docs/
    MODEL_CHECK.md, ARCHITECTURE.md
  tests/
```

## 7. Starter files

**CLAUDE.md**

```markdown
# Farmer Advisory Assistant
Purpose: Tamil/Hindi/English crop, irrigation, fertilizer Q&A, grounded in curated documents.

## Rules (strict)
1. Read TODO.md and WORK.md before starting. Update both after every task.
2. Never invent model names, checkpoints, URLs or dosages. Verify checkpoints exist before use.
3. Answers must come only from retrieved chunks. No source -> say so, do not guess.
4. Model names, paths, top_k live in config.yaml only.
5. Touch only the files the task needs. No whole-repo rewrites.
6. One module per commit. Run its tests before marking it done.

## Architecture
detect lang -> IndicTrans2 to English -> router (answer|clarify|refuse)
-> hybrid retrieve top 5 -> AgriParam grounded answer + citations
-> IndicTrans2 back -> Gradio UI with sources panel.

## Stack
Python 3.11, transformers, IndicTrans2, sentence-transformers, ChromaDB,
rank_bm25, Gradio, pytest.
```

**TODO.md**

```markdown
# TODO.md
## ingest
- [ ] extract text from raw docs
- [ ] translate non-English docs to English
- [ ] chunk and write chunks.jsonl
## translate
- [ ] IndicTrans2 wrapper + glossary
## retrieval
- [ ] embeddings + Chroma + BM25 hybrid
## agent
- [ ] router
- [ ] grounded generation + citations
## app
- [ ] Gradio UI
## eval
- [ ] 40 cases, metrics, judge, report
```

**WORK.md**

```markdown
# WORK.md
2026-11-05  Phase 0  Repo created. (model used, what changed, what is next)
```
