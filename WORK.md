# WORK.md
Dated log of finished tasks: date | phase | model | what changed | next.

2026-11-05 | Phase 0 | Opus 5.5 | Created CLAUDE.md, TODO.md, WORK.md from BUILD_PLAN.md s7 and the kickoff rules. Found Python 3.11 not installed (3.12 and 3.14 are); using 3.12. | Next: repo layout, venv.
2026-11-05 | Phase 0 | Opus 5.5 | Verified all checkpoints exist on HF (AgriParam 2.86B, 2048 ctx; IndicTrans2 dist-200M gated; bge-m3). Layout, config.yaml, src/config.py, venv. IndicTransToolkit 1.1.1 won't build on Windows (no MSVC): vendored pure-Python v1.0.2 IndicProcessor. | Next: model load checks.
2026-11-05 | Phase 0 | Opus 5.5 | Pinned requirements, config tests pass (3). Downloaded bge-m3 + AgriParam. Checks: bge-m3 OK (2.28 GB, cross-lingual 0.77 vs 0.29); AgriParam OK in bf16 (5.85 GB) but KV cache crashes, works with use_cache=False. IndicTrans2 download 403: terms not accepted on HF. | Next: user accepts IndicTrans2 terms, then translation check.
