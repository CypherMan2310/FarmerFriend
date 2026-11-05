"""Router tests: answer / clarify / refuse, using fake retrieved chunks (offline)."""

from src.agent.generate import ground_answer
from src.agent.router import route
from src.config import load_config

CFG = load_config()
AGRI = [{"text": "Apply 120 kg N per hectare to wheat in three splits. Irrigate at crown root "
                 "initiation.", "dense_sim": 0.72}]
PEST = [{"text": "Spray imidacloprid 17.8 SL at 100 ml per acre against aphids.", "dense_sim": 0.7}]
OFF = [{"text": "Apply 120 kg N per hectare to wheat.", "dense_sim": 0.21}]


def test_answers_in_domain_question_with_crop() -> None:
    assert route("How much nitrogen for wheat?", "", "en", AGRI, CFG).action == "answer"


def test_clarifies_when_crop_missing() -> None:
    assert route("How much fertilizer should I apply?", "", "en", AGRI, CFG).action == "clarify"


def test_crop_from_native_glossary_counts() -> None:
    # Translation lost the crop name, but the Hindi text names wheat (गेहूं).
    d = route("How much fertilizer should I apply?", "गेहूं में कितना उर्वरक डालें?", "hi", AGRI, CFG)
    assert d.action == "answer"


def test_refuses_out_of_domain() -> None:
    assert route("Who won the cricket world cup?", "", "en", OFF, CFG).action == "refuse"


def test_refuses_unsourced_pesticide_dose() -> None:
    d = route("How much endosulfan should I spray on cotton?", "", "en", AGRI, CFG)
    assert d.action == "refuse" and "dose" in d.reason


def test_allows_pesticide_dose_present_in_source() -> None:
    assert route("How much imidacloprid per acre for aphids on cotton?", "", "en", PEST,
                 CFG).action == "answer"


def test_grounding_drops_unsupported_figures() -> None:
    kept = ground_answer("Apply 120 kg N per hectare to wheat [1]. Apply 200 kg N per hectare "
                         "to wheat [1].", AGRI)
    assert len(kept) == 1 and "120" in kept[0]["text"] and kept[0]["cite"] == 1
