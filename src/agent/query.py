"""Turn a user question into (language, English query, original text) for retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.translate.glossary import augment_query
from src.translate.langdetect import detect_language


@dataclass
class PreparedQuery:
    """A user question after language detection and translation to English."""

    lang: str
    native: str
    english: str


def prepare_query(text: str, translator: Any, lang: str | None = None) -> PreparedQuery:
    """Detect language (unless given), translate to English and add glossary terms."""
    text = text.strip()
    lang = lang or detect_language(text)
    if lang == "en":
        return PreparedQuery("en", text, text)
    english = translator.translate([text], lang, "en")[0]
    return PreparedQuery(lang, text, augment_query(english, text, lang))
