"""Rebuild everything the app needs, skipping steps whose output already exists.

Steps: download models -> download sources -> extract -> translate Tamil/Hindi pages ->
chunk -> Chroma index. Usage: python scripts/build_data.py [--force]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.config import load_config, repo_path  # noqa: E402


def run(*cmd: str) -> None:
    """Run a Python module/script with the current interpreter; stop on failure."""
    print(f"==> {' '.join(cmd)}", flush=True)
    subprocess.run([sys.executable, *cmd], cwd=ROOT, check=True)


def main() -> None:
    """Run the missing build steps in order."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    force = ap.parse_args().force
    p = load_config()["paths"]
    run("scripts/download_models.py")
    run("scripts/download_sources.py")
    if force or not repo_path(p["extracted"]).exists():
        run("-m", "src.ingest.extract")
    run("-m", "src.ingest.translate_docs")  # resumable: only untranslated pages
    if force or not repo_path(p["chunks"]).exists():
        run("-m", "src.ingest.chunk")
    if force or not (repo_path(p["index_dir"]) / "chroma").exists():
        run("-m", "src.retrieval.index")
    print("build complete")


if __name__ == "__main__":
    main()
