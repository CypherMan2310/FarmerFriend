# TODO.md
Tick a box only after that module's test passes. Claude model in [brackets].

## Phase 0: setup
- [x] CLAUDE.md, TODO.md, WORK.md [Opus]
- [x] repo layout, git init, .gitignore [Haiku]
- [x] venv + requirements.txt (pinned) [Haiku]
- [x] config.yaml + src/config.py loader + tests/test_config.py [Sonnet]
- [x] verify AgriParam + bge-m3 on this machine -> docs/MODEL_CHECK.md [Opus]
- [x] vendored IndicProcessor + offline test [Opus]
- [ ] BLOCKED (user: HF token needs gated-repo read): IndicTrans2. NLLB-200 fallback in use.

## Phase 1: ingest
- [x] 36 candidate sources researched; 34 kept (data/sources.jsonl, data/SOURCES.md) [Sonnet]
- [x] scripts/download_sources.py -> data/raw/ [Haiku]
- [x] extract.py with legacy-font script check [Sonnet]
- [x] translate_docs.py (102 ta/hi pages, NLLB) [Opus]
- [x] chunk.py: 300 AgriParam tokens -> data/chunks.jsonl (3042 chunks) [Sonnet]
- [x] tests/test_ingest.py

## Phase 2: translate
- [x] langdetect.py, glossary.py, indictrans.py (IndicTrans2 | NLLB) [Opus]
- [x] tests/test_translate.py: 10 questions round-trip ta (chrF 48.5) and hi (61.6)
- [ ] diff vendored IndicProcessor v1.0.2 vs 1.1.1 (only matters once IndicTrans2 is accessible)

## Phase 3: retrieval
- [x] embed.py, index.py (Chroma), hybrid.py (dense en + native, BM25, RRF) [Opus]
- [x] 15 hand-labelled queries: hit@5 15/15 (eval/retrieval_report.md)
- [x] tests/test_retrieval.py

## Phase 4: agent
- [x] prompts.py, router.py, generate.py (tuple-cache greedy loop), pipeline.py [Opus]
- [x] CLI answers 10 queries in ta/hi/en (eval/cli_run.md)
- [x] tests/test_router.py

## Phase 5: app
- [x] gradio_app.py: chat, language selector, sources panel, thumbs log [Sonnet]
- [x] run.ps1 / run.sh one-command run; scripts/build_data.py

## Phase 6: eval
- [x] cases.jsonl (40) + cases.py loader, metrics.py, judge.py, run_eval.py [Opus]
- [x] report.md with results and failure analysis [Opus medium]

## Phase 7: polish
- [x] README, docs/ARCHITECTURE.md, scripts/demo.py [Sonnet]
- [x] tag v1.0 [Haiku]
