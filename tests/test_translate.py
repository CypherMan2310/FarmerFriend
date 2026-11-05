"""Tests for language detection, glossary and the translator (10 questions, ta and hi)."""

import json
from pathlib import Path

import pytest

from src.translate.glossary import augment_query, english_terms, figures, missing_figures
from src.translate.langdetect import detect_language

QUESTIONS = [json.loads(x) for x in (Path(__file__).parent / "data" / "roundtrip_questions.jsonl")
             .read_text(encoding="utf-8").splitlines() if x.strip()]


def test_detect_language() -> None:
    for q in QUESTIONS:
        assert detect_language(q["en"]) == "en"
        assert detect_language(q["hi"]) == "hi"
        assert detect_language(q["ta"]) == "ta"


def test_glossary_terms_and_figures() -> None:
    assert "wheat" in english_terms(QUESTIONS[0]["hi"], "hi")
    assert "paddy rice" in english_terms(QUESTIONS[1]["ta"], "ta")
    assert "wheat" in augment_query("When to water the crop?", QUESTIONS[0]["hi"], "hi")
    assert figures("१२० किग्रा, 60.5 kg and 1,000") == ["120", "60.5", "1000"]
    assert missing_figures("Apply 120 kg N", "120 கிலோ") == []
    assert missing_figures("Apply 120 kg N", "நூற்று இருபது") == ["120"]


@pytest.fixture(scope="module")
def translator():
    from src.translate.indictrans import Translator

    try:
        return Translator()
    except RuntimeError as exc:
        pytest.skip(f"no translation backend: {exc}")


@pytest.mark.parametrize("lang", ["ta", "hi"])
def test_roundtrip_10_questions(translator, lang: str) -> None:
    from sacrebleu.metrics import CHRF

    native = [q[lang] for q in QUESTIONS]
    english = translator.translate(native, lang, "en")
    back = translator.translate(english, "en", lang)
    assert all(detect_language(e) == "en" for e in english)
    assert all(detect_language(b) == lang for b in back)
    chrf = CHRF().corpus_score(back, [native]).score
    print(f"\n{lang} backend={translator.backend} round-trip chrF={chrf:.1f}")
    for n, e in zip(native[:3], english[:3]):
        print(f"  {n} -> {e}")
    assert chrf > 30


def test_answer_keeps_figures(translator) -> None:
    out = translator.translate_answer("Apply 120 kg nitrogen per hectare in three splits.", "hi")
    assert "120" in out
