"""Pre-download the checkpoints named in config.yaml into the Hugging Face cache.

Usage:
    python scripts/download_models.py [--only llm translation embedding] [--with-fallbacks]

IndicTrans2 repos are gated: log in first (`hf auth login` or HF_TOKEN env var) with an
account that has accepted their terms on huggingface.co.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config  # noqa: E402

# Skip duplicate weight formats we never load.
IGNORE = ["onnx/*", "openvino/*", "imgs/*", "*.onnx", "*.onnx_data", "*.png", "*.jpg"]
IGNORE_IF_SAFETENSORS = ["pytorch_model.bin"]


def model_ids(cfg: dict, roles: list[str], with_fallbacks: bool) -> list[str]:
    """List checkpoint IDs for the requested roles, primary first."""
    m = cfg["models"]
    ids: list[str] = []
    if "llm" in roles:
        ids.append(m["llm"]["primary"])
        if with_fallbacks:
            ids += m["llm"]["fallbacks"]
    if "translation" in roles:
        ids += [m["translation"]["indic_en"], m["translation"]["en_indic"]]
        if with_fallbacks:
            ids += list(m["translation"]["fallbacks"].values())
    if "embedding" in roles:
        ids.append(m["embedding"]["primary"])
        if with_fallbacks:
            ids += m["embedding"]["fallbacks"]
    return ids


def main() -> None:
    """Download each checkpoint; report failures without stopping the others."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", default=["embedding", "translation", "llm"],
                    choices=["llm", "translation", "embedding"])
    ap.add_argument("--with-fallbacks", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    failed = []
    for repo in model_ids(cfg, args.only, args.with_fallbacks):
        print(f"[download] {repo}", flush=True)
        try:
            ignore = IGNORE + (IGNORE_IF_SAFETENSORS if "indictrans2" in repo else [])
            path = snapshot_download(repo, ignore_patterns=ignore)
            print(f"[ok] {repo} -> {path}", flush=True)
        except Exception as exc:  # gated repo, network, disk
            failed.append(repo)
            print(f"[fail] {repo}: {type(exc).__name__}: {str(exc)[:200]}", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
