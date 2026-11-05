"""Load config.yaml, the single source for model names, paths, top_k and languages."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config.yaml"

REQUIRED_SECTIONS = ("languages", "models", "retrieval", "paths")


@lru_cache(maxsize=4)
def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Read and validate a config file.

    Args:
        path: Path to a YAML config. Defaults to the repo's config.yaml.

    Returns:
        The parsed config as a nested dict.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a required top-level section is missing.
    """
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    missing = [s for s in REQUIRED_SECTIONS if s not in cfg]
    if missing:
        raise ValueError(f"{path} is missing sections: {missing}")
    return cfg


def repo_path(relative: str) -> Path:
    """Resolve a path from config.yaml (relative to the repo root) to an absolute path."""
    return REPO_ROOT / relative
