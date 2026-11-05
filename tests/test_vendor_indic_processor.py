"""Offline smoke test for the vendored IndicTrans2 pre/post-processor (no model weights needed)."""

from src.translate._vendor.indic_processor import IndicProcessor


def test_preprocess_adds_language_tags() -> None:
    ip = IndicProcessor(inference=True)
    samples = {
        "hin_Deva": "गेहूं की फसल में सिंचाई कब करनी चाहिए?",
        "tam_Taml": "நெல் பயிருக்கு எப்போது நீர் பாய்ச்ச வேண்டும்?",
    }
    for src, text in samples.items():
        out = ip.preprocess_batch([text], src_lang=src, tgt_lang="eng_Latn")
        assert len(out) == 1
        assert out[0].startswith(f"{src} eng_Latn ")


def test_postprocess_returns_one_string_per_input() -> None:
    ip = IndicProcessor(inference=True)
    ip.preprocess_batch(["When should I irrigate wheat?"], src_lang="eng_Latn", tgt_lang="hin_Deva")
    out = ip.postprocess_batch(["गेहूं की सिंचाई कब करें?"], lang="hin_Deva")
    assert len(out) == 1 and out[0].strip()
