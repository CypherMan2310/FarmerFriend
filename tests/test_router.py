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


def test_extractive_quotes_only_chunks_about_the_asked_crop() -> None:
    import numpy as np

    from src.agent.generate import extractive_answer
    from src.agent.router import CROPS

    def embed(texts: list[str]) -> np.ndarray:
        v = np.array([[("irrigat" in t.lower() or "water" in t.lower()) * 1.0,
                       ("gypsum" in t.lower()) * 1.0, 0.1] for t in texts])
        return v / np.linalg.norm(v, axis=1, keepdims=True)

    chunks = [{"text": "Groundnut: irrigate at pegging and apply gypsum 400 kg per ha at 40 days."},
              {"text": "Banana: irrigate immediately after planting; give life irrigation after 4 days."}]
    out = extractive_answer("When should water be given to banana?", chunks, embed, CROPS, k=1)
    assert len(out) == 1 and out[0]["cite"] == 2 and "life irrigation" in out[0]["text"]


def test_question_headings_are_never_answers() -> None:
    from src.agent.generate import is_statement

    assert not is_statement("What is the best method for direct sowing in tarwatt fields?")
    assert not is_statement("Irrigation Management")
    assert is_statement("Give life irrigation after 4 days after planting banana.")
    assert ground_answer("What is the dose of N for wheat? [1]", AGRI) == []
