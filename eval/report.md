# Evaluation report

40 cases (`eval/cases.jsonl`): 10 crop, 8 irrigation, 8 fertilizer, 6 clarification,
8 refuse; 15 Tamil, 15 Hindi, 10 English. Run with `python eval/run_eval.py`; per-case
output in `eval/metrics.md` (earlier runs: `metrics_run1.md`, `metrics_run2.md`).

**System under test (run 3, final):** quote-first answers (the source sentences most similar
to the question, ranked by bge-m3, restricted to chunks that mention the crop asked, quoted
verbatim with citations) with AgriParam generation as fallback; NLLB-200 600M translation
(IndicTrans2 was not accessible: gated repo, token lacked permission); bge-m3 + BM25 hybrid
retrieval; rule-based router. RTX 4060 Laptop 8 GB.

**Gold answers.** The plan asked for gold answers written by hand. The user asked Claude to
finish without further input, so Claude wrote the 2-4 key facts per case by copying them from
one source document (each case stores the document and an exact evidence phrase, verified to
exist in the chunks). They were not written by the user.

**Judge.** No external LLM API was available. `judge.py` combines a lexical check (word
overlap >= 0.5 with the cited chunk, every figure present) with AgriParam asked "does the
context state this claim? yes/no". Claude then read all final answers (manual check).

## Results

| Metric | Run 1 | Run 2 | Run 3 (final) |
| --- | --- | --- | --- |
| Retrieval hit@5 (exact evidence passage in top 5, 26 answer cases) | 0.46 | 0.46 | 0.46 |
| Groundedness, AgriParam judge (answer sentences) | 0.14 | 0.11 | 0.31 |
| Groundedness, lexical judge | - | 1.00 | 1.00 |
| Groundedness, manual | - | 0.41 | 1.00 (all sentences are verbatim quotes) |
| Answers the question, manual (26 answer cases) | - | - | 0.50 (13) + 3 partial |
| Factual correctness (gold facts present) | 0.06 | 0.14 | 0.22 |
| Domain QA accuracy | 0.33 | 0.45 | **0.525** |
| Router accuracy | 0.90 | 0.975 | **0.975** |
| No-source rate on answer cases | 0.15 | 0.15 | 0.00 |
| Back-translation chrF (30 ta/hi questions) | 54.7 | 54.7 | 54.7 |
| Median latency per question | 3.65 s | 3.74 s | 7.45 s |

Phase 3 retrieval on its own 15 hand-labelled queries (document-level hit with a key term):
**hit@5 = 15/15** after one glossary fix (`eval/retrieval_report.md`).

Changes between runs:
- **Run 1 to 2:** router requires a farming keyword; scheme/subsidy questions skip
  clarification; sentence-level figure grounding; 3-gram repetition blocking; extractive
  fallback.
- **Run 2 to 3:** quote-first answers with a crop filter; question-shaped sentences (FAQ
  headings) are never used as answers. After run 3, identical sentences repeated by
  overlapping chunks are de-duplicated (presentation only).

**Reading the numbers.** Factual correctness and QA accuracy undercount: gold facts come from
one document, but several answers quote a different valid source (c04 PAU mustard sowing
dates, i03 PAU first irrigation, f01 PAU wheat dose, f02 PAU zinc dose). The AgriParam judge
rejects many verbatim quotes, so it understates groundedness. The manual columns are the best
estimate. The no-source rate dropped to 0: the system now quotes the closest passage even when
it is only loosely related, instead of saying it has no source (see limitations).

## Failure analysis (run 3, manual tags)

| Cause | Cases | Ids |
| --- | --- | --- |
| Translation error (query mistranslated, wrong passage quoted) | 6 | c08, c09, c10, f06, f07, f08 (all Tamil) |
| Retrieval miss (query fine, right passage not in top 5) | 3 | c06, f04, i08 |
| Other: right passage, wrong sentence chosen | 3 | c05, i04, c01 (table header only) |
| Unit or dosage error (figure from another crop's context) | 1 | f03 |
| Wrong router action | 1 | x04 |
| Hallucination | 0 | (answers are verbatim quotes; run 2 had 5) |

### Worked examples

1. **Translation error (f07, Tamil).** "How much zinc to prevent zinc deficiency in rice?"
   became "How much tissue is needed to prevent a nail defect?". Retrieval found nothing about
   zinc and the answer quoted a nursery-spacing sentence. Fix tried: the glossary appends
   "(paddy rice)" but has no nutrient terms. The same kind of error in Phase 3 (Hindi "चने",
   chickpea, rendered as "seedling") was fixed by a glossary entry, raising hit@5 from 14/15 to
   15/15. Next: add nutrient and practice terms to the Tamil glossary, or use IndicTrans2
   once the Hugging Face token can read gated repos.
2. **Wrong router action (x05 in run 1, x04 now).** "I have a fever, which medicine?" had no
   farming keyword but 0.60 similarity to a pesticide-poisoning first-aid passage, so run 1
   answered with antidote doses. Fix: a farming keyword is required (router accuracy
   0.90 to 0.975). The remaining error, x04, is translation-driven: "मोनोक्रोटोफॉस" became
   "monocrotophose", which the pesticide list does not match, so a dose question that should
   be refused went to the answer path (no dose was shown in runs 2 and 3, but it was not
   refused).
3. **Generation and selection errors (c04 and the repeated answer).** In run 2 AgriParam
   wrote "The sowing time of sowing is between October to October" for mustard (the source says
   10-25 October). Quote-first answering fixed this: run 3 quotes the PAU sowing-date table.
   The first quote-first version then answered many questions with the same FAQ heading,
   "What is the best method for direct sowing in tar-wattar fields?", because question-shaped
   sentences are similar to every question. Fix: sentences ending in "?" or shorter than six
   words are never answers (`is_statement`, tested).
4. **Wrong-crop figure (f03).** The Hindi question about direct-seeded rice was translated with
   "strawberries"; one quoted sentence gives a wheat seed and DAP dose. The figure is exact in
   its source, but it is about another crop. The crop filter only applies when a crop name
   survives translation.

## Limitations

- Tamil translation through NLLB is the weakest link: 6 of the 13 failures, and answers
  translated back into Tamil are often hard to read (figures are kept exact).
- Quote-first answers are faithful but can be long or tangential, and the system now rarely
  says "no source"; a higher similarity threshold would trade coverage for precision.
- AgriParam (2.9 B, 2048 tokens) is only used as a fallback because its paraphrases were
  often garbled; it also ignored the citation format.
- Gold facts and the manual check were done by Claude from the sources, not by an agronomist
  or the user. The LLM judge (AgriParam) was unreliable.
- The corpus is 34 documents; most are "all rights reserved" and used only locally.
