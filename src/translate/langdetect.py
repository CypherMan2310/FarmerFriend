"""Detect Tamil, Hindi or English from Unicode script. No model."""

from __future__ import annotations

TAMIL = (0x0B80, 0x0BFF)
DEVANAGARI = (0x0900, 0x097F)


def detect_language(text: str) -> str:
    """Return "ta", "hi" or "en" by majority script among letters (default "en")."""
    ta = hi = latin = 0
    for ch in text:
        o = ord(ch)
        if TAMIL[0] <= o <= TAMIL[1]:
            ta += 1
        elif DEVANAGARI[0] <= o <= DEVANAGARI[1]:
            hi += 1
        elif ch.isascii() and ch.isalpha():
            latin += 1
    if max(ta, hi) == 0 or (latin > ta and latin > hi):
        return "en"
    return "ta" if ta >= hi else "hi"
