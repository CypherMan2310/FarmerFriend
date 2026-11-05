# Retrieval evaluation (Phase 3)

Hybrid retriever (bge-m3 dense on English + original query, BM25, RRF), translator backend `nllb`. Hit = a top-5 chunk from a gold document containing a gold term. Labels were set by hand from the source documents.

**hit@5 = 15/15 = 1.00** (en 5/5, hi 5/5, ta 5/5)

| id | lang | query | English query used | gold docs | top-5 docs | hit |
| --- | --- | --- | --- | --- | --- | --- |
| r01 | en | At which growth stages should wheat be irrigated? | At which growth stages should wheat be irrigated? | icar01, open12 | tn01, open12, open12, icar01, open08 | yes |
| r02 | en | What are the steps for successful rice production? | What are the steps for successful rice production? | open05 | open05, open05, open05, open05, open05 | yes |
| r03 | en | What financial assistance is available for drip irrigation under Per Drop More Crop? | What financial assistance is available for drip irrigation under Per Drop More Crop? | icar06 | icar06, icar06, icar06, icar06, icar06 | yes |
| r04 | en | What is the seed rate for direct seeded rice? | What is the seed rate for direct seeded rice? | icar07, open08, open11 | open11, open07, open07, icar07, open07 | yes |
| r05 | en | How to correct zinc deficiency in rice? | How to correct zinc deficiency in rice? | open06, open11, tn02, tn10 | open11, open06, open09, open06, open11 | yes |
| r06 | hi | रबी मक्का की बुवाई कब करें? | When to sow Rabi Mecca? (maize) | icar03 | icar03, icar03, icar03, icar03, icar03 | yes |
| r07 | hi | कपास में उर्वरक की सिफारिश कैसे करें? | How to recommend fertilizer in cotton? | icar05, open11, tn08 | icar05, open06, tn08, tn08, open11 | yes |
| r08 | hi | सरसों की उपज कैसे बढ़ाएं? | How to increase the yield of mustard? | icar08, open12 | icar08, icar08, icar08, icar08, icar08 | yes |
| r09 | hi | चने की बुवाई में पौधों के बीच कितनी दूरी रखें? | How much distance should be kept between the plants in the seedling? (chickpea) | open09, open12 | open09, tn11, open09, open09, open09 | yes |
| r10 | hi | ड्रिप सिंचाई के क्या लाभ हैं? | What are the benefits of drip irrigation? | icar02, icar04, tn03, open01 | icar04, icar04, icar04, icar02, tn03 | yes |
| r11 | ta | கரும்புக்கு உரம் எப்போது இட வேண்டும்? | When should yeast be allowed to ferment? (sugarcane, fertilizer) | tn04, tn06 | tn06, open11, open12, open12, tn04 | yes |
| r12 | ta | நெல் வயலில் நீர் மேலாண்மை எப்படி செய்வது? | How to manage water in a rice field? (paddy rice) | tn01, open05, open01, icar07 | open01, open04, open11, open11, open05 | yes |
| r13 | ta | நிலக்கடலைக்கு ஜிப்சம் எப்போது இட வேண்டும்? | When should gypsum be placed on the mainland? (groundnut) | tn07, open11 | tn07, tn07, open11, open11, open11 | yes |
| r14 | ta | வாழைக்கு சொட்டு நீர் பாசனம் எவ்வளவு கொடுக்க வேண்டும்? | How much should a drop of water be poured for a banana? (drip irrigation) | tn05, tn11, tn03 | tn03, tn06, tn05, tn09, icar11 | yes |
| r15 | ta | துவரையை கோதுமையுடன் சுழற்சி முறையில் பயிரிடலாமா? | Is it possible to rotate the crop with wheat? (pigeonpea redgram) | open10 | open10, open10, open10, open10, open10 | yes |

## History

- First run: hit@5 = 14/15 (hi 4/5). Miss r09: the translator rendered Hindi "चने" (inflected
  form of chickpea) as "seedling", so the crop vanished from the English query (translation
  error). Fix: added the inflected form "चने" to `src/translate/glossary.py`, which appends
  "(chickpea)" to the query. Second run (table above): 15/15.
