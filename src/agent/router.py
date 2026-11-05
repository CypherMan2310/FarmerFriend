"""Rule-based router: answer, clarify (no crop for crop-specific advice) or refuse.

Refuse when the question is outside crops/irrigation/fertilizer, or when it asks for a
pesticide/chemical dose that no retrieved chunk states.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from src.translate.glossary import english_terms

CROPS = set("""wheat rice paddy maize corn cotton sugarcane mustard rapeseed chickpea gram
pigeonpea redgram arhar tur soybean groundnut peanut banana tomato millet sorghum jowar ragi
bajra greengram blackgram moong urad coconut onion potato pulse pulses barley lentil sunflower
sesame""".split())
DOMAIN = CROPS | set("""crop crops farm farmer farming field soil seed seeds sow sowing plant
plants planting irrigation irrigate water watering drip sprinkler fertilizer fertiliser
fertilizers manure compost urea dap potash nitrogen phosphorus potassium zinc nutrient
nutrients yield harvest variety varieties weed weeds pest pests disease spray pesticide
insecticide fungicide herbicide agriculture kharif rabi acre hectare organic mulch nursery
transplant transplanting tillage germination rainfed micronutrient gypsum lime""".split())
SPECIFIC = ("how much", "how many", "dose", "dosage", "quantity", "seed rate", "spacing",
            "schedule", "how often", "when should", "when to", "when do", "what time",
            "which variety", "varieties", "which fertilizer", "what fertilizer",
            "fertilizers should", "how to apply", "best time")
PESTICIDES = set("""pesticide pesticides insecticide insecticides fungicide fungicides herbicide
herbicides weedicide chemical chemicals poison spray chlorpyrifos endosulfan monocrotophos
imidacloprid glyphosate paraquat mancozeb carbendazim malathion cypermethrin quinalphos acephate
dimethoate carbofuran phorate atrazine fipronil thiamethoxam profenofos emamectin
chlorantraniliprole""".split())
DOSE = ("how much", "dose", "dosage", "quantity", " ml", "litre", "liter", "mix", "per acre",
        "per hectare", "concentration", "how many grams")
SCHEME = set("scheme schemes subsidy assistance support government policy loan insurance".split())
_UNIT = re.compile(r"\d\s*(ml|g|gm|kg|l|litre|liter|%)\b", re.I)
_W = re.compile(r"[a-z]+")


@dataclass
class Decision:
    """Router output."""

    action: str  # "answer" | "clarify" | "refuse"
    reason: str


def route(query_en: str, native: str, lang: str, retrieved: list[dict[str, Any]],
          cfg: dict[str, Any]) -> Decision:
    """Choose the action for a question given its English form and retrieved chunks."""
    q = query_en.lower()
    words = set(_W.findall(q)) | {w for t in english_terms(native, lang) for w in t.split()}
    best_sim = max((c.get("dense_sim", 0.0) for c in retrieved), default=0.0)
    r = cfg["router"]

    pest = words & PESTICIDES
    if pest and any(d in f" {q}" for d in DOSE):
        named = pest - {"pesticide", "pesticides", "insecticide", "insecticides", "fungicide",
                        "fungicides", "herbicide", "herbicides", "weedicide", "chemical",
                        "chemicals", "spray", "poison"}
        terms = named or pest
        # A dose counts as sourced only if a figure with a unit appears within 120
        # characters after the pesticide name in a retrieved chunk.
        sourced = any(_UNIT.search(m.group(0)) for c in retrieved for t in terms
                      for m in re.finditer(re.escape(t) + r".{0,120}", c["text"].lower()))
        if not sourced:
            return Decision("refuse", f"dose for {sorted(terms)} not stated in any retrieved source")

    # A farming keyword is required: similarity alone let medical questions through to
    # pesticide-poisoning passages in the corpus.
    in_domain = bool(words & DOMAIN)
    if not in_domain or best_sim < r["ood_min_sim"]:
        return Decision("refuse", f"out of domain (keywords={in_domain}, best_sim={best_sim:.2f})")

    if not (words & CROPS) and not (words & SCHEME) and any(s in q for s in SPECIFIC):
        return Decision("clarify", "crop-specific advice requested but no crop named")
    return Decision("answer", f"in domain (best_sim={best_sim:.2f})")
