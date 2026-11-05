"""Fill ``text_en`` for Tamil/Hindi pages in data/extracted.jsonl (in place, resumable)."""

from __future__ import annotations

import json

from src.config import load_config, repo_path


def run() -> dict[str, int]:
    """Translate every usable non-English page that has no ``text_en`` yet."""
    from src.translate.indictrans import Translator

    cfg = load_config()
    path = repo_path(cfg["paths"]["extracted"])
    records = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    todo = [r for r in records if r["language"] != "en" and r.get("text_ok") and not r.get("text_en")]
    tr = Translator()
    for n, rec in enumerate(todo, 1):
        rec["text_en"] = tr.translate_long(rec["text"], rec["language"], "en")
        rec["translated_by"] = tr.backend
        if n % 10 == 0 or n == len(todo):
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                            encoding="utf-8")
            print(f"translated {n}/{len(todo)} pages", flush=True)
    return {"translated": len(todo), "backend": tr.backend}  # type: ignore[dict-item]


if __name__ == "__main__":
    print(run())
