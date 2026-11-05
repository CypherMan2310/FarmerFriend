"""Pre-download the checkpoints named in config.yaml into the Hugging Face cache.

Usage:
    python scripts/download_models.py [--only llm translation embedding]

For each role the candidates are tried in config order and the role succeeds when one
downloads (e.g. gated IndicTrans2 fails without access, NLLB-200 is then used).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import load_config  # noqa: E402

IGNORE = ["onnx/*", "openvino/*", "imgs/*", "*.onnx", "*.onnx_data", "*.png", "*.jpg",
          "flax*", "tf_*", "*.msgpack", "*.h5"]


def candidates(cfg: dict, role: str) -> list[list[str]]:
    """Groups of repos per role; a group succeeds only if all its repos download."""
    m = cfg["models"]
    if role == "llm":
        return [[x] for x in [m["llm"]["primary"], *m["llm"]["fallbacks"]]]
    if role == "embedding":
        return [[x] for x in [m["embedding"]["primary"], *m["embedding"]["fallbacks"]]]
    t = m["translation"]
    groups = {"indictrans2": [t["indic_en"], t["en_indic"]], "nllb": [t["nllb"]]}
    return [groups[b] for b in t["backend_order"]]


def main() -> None:
    """Download the first working candidate for each role."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", default=["embedding", "translation", "llm"],
                    choices=["llm", "translation", "embedding"])
    args = ap.parse_args()
    cfg = load_config()
    failed_roles = []
    for role in args.only:
        for group in candidates(cfg, role):
            try:
                for repo in group:
                    ignore = IGNORE + (["pytorch_model.bin"] if "indictrans2" in repo else [])
                    snapshot_download(repo, ignore_patterns=ignore)
                print(f"[ok] {role}: {', '.join(group)}", flush=True)
                break
            except Exception as exc:  # gated repo, network, disk
                print(f"[skip] {role}: {group[0]}: {type(exc).__name__}", flush=True)
        else:
            failed_roles.append(role)
    sys.exit(1 if failed_roles else 0)


if __name__ == "__main__":
    main()
