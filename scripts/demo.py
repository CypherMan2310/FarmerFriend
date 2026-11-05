"""Demo: one question per action and language, printed with answers and cited sources.

Usage: python scripts/demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agent.cli import format_result  # noqa: E402
from src.agent.pipeline import Assistant  # noqa: E402

DEMO = [
    ("Which growth stages of wheat are most critical for irrigation?", "en"),
    ("ड्रिप सिंचाई के क्या लाभ हैं?", "hi"),
    ("வாழைக்கு நீர் பாசனம் எப்போது கொடுக்க வேண்டும்?", "ta"),
    ("How much fertilizer should I apply per acre?", "en"),       # -> clarify
    ("பருத்தியில் எண்டோசல்பான் எவ்வளவு தெளிக்க வேண்டும்?", "ta"),  # -> refuse (unsourced dose)
    ("Who won the cricket world cup in 2011?", "en"),             # -> refuse (out of domain)
]


def main() -> None:
    """Run the demo questions."""
    sys.stdout.reconfigure(encoding="utf-8")
    bot = Assistant()
    for question, lang in DEMO:
        print(format_result(bot.ask(question, lang)), "\n", flush=True)


if __name__ == "__main__":
    main()
