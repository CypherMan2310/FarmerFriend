# TODO.md
Tick a box only after that module's test passes. Claude model in [brackets].

## Phase 0: setup
- [x] CLAUDE.md, TODO.md, WORK.md [Opus]
- [x] repo layout, git init, .gitignore [Haiku]
- [x] venv + requirements.txt (pinned) [Haiku]
- [x] config.yaml + src/config.py loader + tests/test_config.py [Sonnet]
- [ ] verify AgriParam, IndicTrans2, embedding model on this machine -> docs/MODEL_CHECK.md [Opus]

## Phase 1: ingest (data/, src/ingest/)
- [ ] candidate sources, 30-60 docs, only URLs actually opened [Sonnet]
- [ ] data/SOURCES.md: URL + licence per doc; licence allows this use [Sonnet]
- [ ] download to data/raw/ [Haiku]
- [ ] extract.py: text per page [Sonnet]
- [ ] translate_docs.py: non-English pages -> English [Sonnet]
- [ ] chunk.py: 300-500 tokens, metadata doc/page/language -> data/chunks.jsonl [Sonnet]
- [ ] tests/test_ingest.py

## Phase 2: translate (src/translate/)
- [ ] langdetect.py: Unicode script detection ta/hi/en [Sonnet]
- [ ] diff vendored IndicProcessor v1.0.2 against IndicTransToolkit 1.1.1 logic [Opus]
- [ ] glossary.py: crop names + units survive translation [Opus]
- [ ] indictrans.py: IndicTrans2 wrapper with batching [Opus]
- [ ] tests/test_translate.py: 10 questions round-trip in ta and hi

## Phase 3: retrieval (src/retrieval/)
- [ ] embed.py [Opus]
- [ ] index.py: Chroma + BM25 build [Opus]
- [ ] hybrid.py: merge dense + BM25 [Opus]
- [ ] 15 hand-labelled queries, report hit@5 [Sonnet queries, Opus metric]
- [ ] tests/test_retrieval.py

## Phase 4: agent (src/agent/)
- [ ] prompts.py: grounded prompt + citation format [Opus]
- [ ] router.py: answer | clarify | refuse; out-of-domain and unsourced-dose refusal [Opus]
- [ ] generate.py: grounded answer, no-source fallback, figure-citation check [Opus]
- [ ] CLI answers 10 queries across ta/hi/en [Sonnet]
- [ ] tests/test_router.py

## Phase 5: app (src/app/)
- [ ] gradio_app.py: single page, chat, language selector, sources panel [Sonnet]
- [ ] thumbs up/down -> local log file [Sonnet]
- [ ] runs from a fresh clone with one command [Sonnet]

## Phase 6: eval (eval/)
- [ ] cases.jsonl template + loader; user writes gold answers [Sonnet]
- [ ] metrics.py: hit@5, groundedness, factual correctness, QA accuracy, router accuracy,
      back-translation chrF, median latency [Opus]
- [ ] judge.py: LLM judge [Opus]
- [ ] run_eval.py [Opus]
- [ ] report.md: results table + failure analysis (tags, counts, 2-3 examples) [Opus medium]

## Phase 7: polish
- [ ] README: setup, usage, architecture diagram, results, limitations [Sonnet]
- [ ] docs/ARCHITECTURE.md [Sonnet]
- [ ] demo script [Sonnet]
- [ ] remove dead code [Sonnet]
- [ ] tag v1.0 [Haiku]
