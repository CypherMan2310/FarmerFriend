"""Tests for src.config."""

from pathlib import Path

import pytest

from src.config import load_config, repo_path


def test_default_config_has_required_values() -> None:
    cfg = load_config()
    assert cfg["languages"]["supported"] == ["ta", "hi", "en"]
    assert isinstance(cfg["retrieval"]["top_k"], int) and cfg["retrieval"]["top_k"] > 0
    assert cfg["models"]["llm"]["primary"]
    assert cfg["models"]["translation"]["indic_en"]
    assert cfg["models"]["embedding"]["primary"]


def test_missing_section_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("languages: {}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(bad)


def test_repo_path_is_absolute() -> None:
    assert repo_path("data/raw").is_absolute()
