# Evaluation report

40 cases (`eval/cases.jsonl`): 10 crop, 8 irrigation, 8 fertilizer, 6 clarification,
8 refuse; 15 Tamil, 15 Hindi, 10 English. Run with `python eval/run_eval.py`; per-case
output in `eval/metrics.md`, raw results in `eval/results.jsonl`.

**System under test:** AgriParam (bf16, greedy decoding with repetition blocking), NLLB-200
600M for translation (IndicTrans2 was not accessible: gated repo, token lacked permission),
bge-m3 + BM25 hybrid retrieval, rule-based router. RTX 4060 Laptop 8 GB.

**Gold answers.** The plan asked for gold answers written by hand. The user asked Claude to
finish the project without further input, so Claude wrote the 2-4 key facts per case by
copying them from the source documents (each case stores the source document and an exact
evidence phrase, all verified to exist in the chunks). They were not written by the user.

**Judge.** No external LLM API was available. `judge.py` combines (a) a lexical check: word
overlap >= 0.5 with the cited chunk and every figure present, and (b) AgriParam asked
"does the context state this claim? yes/no". Claude then read all 40 final answers
(manual check below).

## Results

| Metric | Run 1 | Run 2 (final) |
| --- | --- | --- |
| Retrieval hit@5 (evidence chunk in top 5, 26 answer cases) | 0.46 | 0.46 |
| Groundedness, lexical judge (final answer sentences) | - | 1.00 (44/44) |
| Groundedness, AgriParam judge (final answer sentences) | 0.14 | 0.11 (5/44) |
| Groundedness, manual (answered cases fully supported and coherent) | - | 0.41 (9/22) |
| Factual correctness (share of gold facts in answer) | 0.06 | 0.14 |
| Domain QA accuracy (right action, right language, >= half the facts) | 0.33 | 0.45 |
| Router accuracy | 0.90 | **0.975** |
| No-source rate on answer cases | 0.15 | 0.15 |
| Back-translation chrF (30 ta/hi questions) | 54.7 | 54.7 |
| Median latency per question | 3.65 s | 3.74 s |

Phase 3 retrieval on its own 15 hand-labelled queries (document-level hit with a key term):
**hit@5 = 15/15** after one glossary fix (`eval/retrieval_report.md`). The eval hit@5 above
is stricter: the specific evidence passage must be in the top 5.

**Run 1 to run 2 changes:** router requires a farming keyword (a fever/medicine question had
been answered from a pesticide-poisoning passage); scheme/subsidy questions are not sent to
clarification; grounding moved from chunk level to sentence level (every figure must sit in
one source sentence that shares >= 50% of the words); 3-gram repetition blocking; when no
generated sentence survives, the answer quotes the best source sentences verbatim.

**The AgriParam judge is unreliable:** it answered "no" for verbatim source quotes (e.g.
i05, f05), so its 0.11 understates groundedness. The lexical judge overstates it (it accepts
garbled sentences built from source words). The manual figure (0.41) is the best estimate.

## Failure analysis (run 2)

Automatic tags (`eval/metrics.md`) depend on the AgriParam judge, so Claude re-checked each
failed case by hand. Manual tags:

| Cause | Cases | Ids |
| --- | --- | --- |
| Translation error | 9 | c07, c08, c09, c10, i03, i08, f03, f06, f07 |
| Hallucination (garbled or unsupported generated text) | 5 | c02, c04, i01, i04, i06 |
| Retrieval miss | 4 | c06, i07, f02, f08 |
| Other (grounded but off-target, or no answer despite a hit) | 4 | c03, c05, f01, f05 |
| Unit or dosage error (figure from the wrong context) | 1 | f04 |
| Wrong router action | 1 | x04 |
| Not a failure on review | 3 | c01 (partly correct), i02, i05 (correct; strict hit rule missed) |

Translation is the largest cause: 8 of the 9 are Tamil. NLLB rendered maize as
"cornstarch", zinc as "tissue", sugarcane trash as "cotton bud", and paddy as "wheat".

### Worked examples

1. **Translation error to no source (f07, Tamil).** Question: how much zinc to prevent zinc
   deficiency in rice. NLLB produced "How much tissue is needed to prevent a nail defect?";
   the glossary only added "(paddy rice)", retrieval found nothing about zinc, and the app
   returned the no-source message (safe but unhelpful). The same failure in Phase 3 (Hindi
   "चने" translated as "seedling") was fixed by adding the inflected form to the glossary,
   which took hit@5 from 14/15 to 15/15. Next fix: add zinc and other nutrient terms to the
   Tamil glossary, or use IndicTrans2 once the token can read gated repos.
2. **Wrong router action, fixed (x05 in run 1).** "I have a fever, which medicine?" had no
   farming keyword but a dense similarity of 0.60 to a pesticide-poisoning first-aid passage,
   so the router answered and quoted antidote doses. Fix: a farming keyword is now required
   before answering. Run 2 refuses it; router accuracy went from 0.90 to 0.975. The one
   remaining router error (x04) is also translation-driven: "मोनोक्रोटोफॉस" became
   "monocrotophose", which the pesticide list did not match, so the question went to the answer
   path. It ended in the no-source message, so no dose was shown, but it should have been
   refused.
3. **Hallucination (c04, Hindi mustard sowing time).** The source says "between 10 and 25
   October"; AgriParam generated "The sowing time of sowing is between October to October".
   The sentence has no figures and shares many words with the source, so the grounding check
   kept it. Fixes tried: sentence-level grounding and repetition blocking (factual correctness
   0.06 to 0.14, QA accuracy 0.33 to 0.45), but garbled paraphrases remain. A related risk
   shows in f04: the figure check guarantees every number appears in the cited source
   sentence, not that the sentence is about the crop asked (a groundnut gypsum timing was
   given for rice). Next steps: quote-first (extractive) answers for dose questions, and a
   stronger instruction-following model or judge.

## Limitations

- AgriParam (2.9 B, 2048-token window) often ignores the citation format and paraphrases
  poorly under greedy decoding; citations are attached after generation by word overlap.
- Tamil translation through NLLB is the weakest link (back-translation chrF 54.7 overall).
- Gold facts were written by Claude from the sources, and the manual check was done by Claude,
  not by an agronomist or the user.
- The corpus is 34 documents; most are "all rights reserved" and used only locally.
