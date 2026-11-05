"""Crop/unit glossary and figure checks so names and numbers survive translation."""

from __future__ import annotations

import re

# Native term -> canonical English term (used to repair/augment translated queries).
GLOSSARY: dict[str, dict[str, str]] = {
    "hi": {
        "गेहूं": "wheat", "गेहूँ": "wheat", "धान": "paddy rice", "चावल": "rice", "मक्का": "maize",
        "कपास": "cotton", "गन्ना": "sugarcane", "गन्ने": "sugarcane", "सरसों": "mustard",
        "चना": "chickpea", "चने": "chickpea", "अरहर": "pigeonpea", "तुअर": "pigeonpea", "सोयाबीन": "soybean",
        "मूंगफली": "groundnut", "केला": "banana", "केले": "banana", "टमाटर": "tomato",
        "बाजरा": "pearl millet", "ज्वार": "sorghum", "मूंग": "greengram", "उड़द": "blackgram",
        "नारियल": "coconut", "प्याज": "onion", "आलू": "potato", "हेक्टेयर": "hectare",
        "एकड़": "acre", "किलोग्राम": "kg", "यूरिया": "urea", "नाइट्रोजन": "nitrogen",
        "फास्फोरस": "phosphorus", "पोटाश": "potash", "सिंचाई": "irrigation", "ड्रिप": "drip",
        "उर्वरक": "fertilizer", "खाद": "manure fertilizer", "बीज दर": "seed rate",
    },
    "ta": {
        "நெல்": "paddy rice", "அரிசி": "rice", "கோதுமை": "wheat", "மக்காச்சோளம்": "maize",
        "பருத்தி": "cotton", "கரும்பு": "sugarcane", "கடுகு": "mustard",
        "கொண்டைக்கடலை": "chickpea", "துவரை": "pigeonpea redgram", "உளுந்து": "blackgram",
        "பாசிப்பயறு": "greengram", "நிலக்கடலை": "groundnut", "வேர்க்கடலை": "groundnut",
        "வாழை": "banana", "தக்காளி": "tomato", "தென்னை": "coconut", "கம்பு": "pearl millet",
        "கேழ்வரகு": "ragi finger millet", "சோளம்": "sorghum", "வெங்காயம்": "onion",
        "ஏக்கர்": "acre", "ஹெக்டேர்": "hectare", "கிலோ": "kg", "யூரியா": "urea",
        "தழைச்சத்து": "nitrogen", "மணிச்சத்து": "phosphorus", "சாம்பல்சத்து": "potassium",
        "உரம்": "fertilizer", "நீர்ப்பாசனம்": "irrigation", "சொட்டு நீர்": "drip irrigation",
        "விதை அளவு": "seed rate",
    },
}

_INDIC_DIGITS = str.maketrans("०१२३४५६७८९௦௧௨௩௪௫௬௭௮௯", "01234567890123456789")
_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def english_terms(text: str, lang: str) -> list[str]:
    """Canonical English terms for glossary entries found in native-language text."""
    found = [en for term, en in GLOSSARY.get(lang, {}).items() if term in text]
    return list(dict.fromkeys(found))


def augment_query(english: str, native: str, lang: str) -> str:
    """Append glossary terms missing from a machine-translated query (helps retrieval)."""
    missing = [t for t in english_terms(native, lang) if t.split()[0] not in english.lower()]
    return english if not missing else f"{english} ({', '.join(missing)})"


def figures(text: str) -> list[str]:
    """Numbers in text, with Indic digits normalised to ASCII and commas removed."""
    return [m.replace(",", "") for m in _NUM.findall(text.translate(_INDIC_DIGITS))]


def missing_figures(source: str, translated: str) -> list[str]:
    """Figures present in ``source`` but absent from ``translated``."""
    have = set(figures(translated))
    return [f for f in figures(source) if f not in have]
