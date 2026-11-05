#!/usr/bin/env bash
# One command from a fresh clone (Linux/macOS):  bash run.sh
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3.12 -m venv .venv
.venv/bin/python -m pip install -q -r requirements.txt
.venv/bin/python scripts/build_data.py
.venv/bin/python -m src.app.gradio_app
