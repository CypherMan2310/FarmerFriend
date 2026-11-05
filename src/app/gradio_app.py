"""Gradio front end: chat, language selector, sources panel, thumbs up/down log.

Run: python -m src.app.gradio_app
"""

from __future__ import annotations

import json
import time
from typing import Any

import gradio as gr

from src.config import load_config, repo_path

LANGS = {"Auto-detect": None, "English": "en", "தமிழ் (Tamil)": "ta", "हिन्दी (Hindi)": "hi"}
DISCLAIMER = ("Answers come only from the listed advisory documents and may contain "
              "translation errors. This is not a substitute for your local agriculture officer.")


def sources_markdown(result: dict[str, Any]) -> str:
    """Render the sources shown for one answer."""
    if not result.get("sources"):
        return f"_No sources (action: {result['action']})._"
    parts = [f"**Action:** `{result['action']}`, {result['latency_s']} s"]
    for s in result["sources"]:
        mark = "cited" if s["cited"] else "retrieved"
        text = s["text"][:700] + ("..." if len(s["text"]) > 700 else "")
        parts.append(f"**[{s['n']}] {s['title']}**, p. {s['page']} ({mark})  \n"
                     f"[{s['url']}]({s['url']})\n\n> {text}")
    return "\n\n".join(parts)


def build_app(bot: Any) -> gr.Blocks:
    """Create the Blocks UI around an ``Assistant``."""
    cfg = load_config()
    log_path = repo_path(cfg["paths"]["feedback_log"])

    def respond(message: str, history: list, lang_label: str, results: list):
        if not message.strip():
            return history, "", gr.update(), results
        r = bot.ask(message, LANGS[lang_label])
        history = history + [{"role": "user", "content": message},
                             {"role": "assistant", "content": r["answer"]}]
        return history, "", sources_markdown(r), results + [r]

    def feedback(data: gr.LikeData, results: list) -> None:
        idx = data.index if isinstance(data.index, int) else data.index[0]
        r = results[idx // 2] if idx // 2 < len(results) else {}
        rec = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "liked": data.liked,
               "question": r.get("question"), "answer": r.get("answer"),
               "lang": r.get("lang"), "action": r.get("action"),
               "sources": [s["chunk_id"] for s in r.get("sources", []) if s.get("cited")]}
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with gr.Blocks(title="Farmer Advisory Assistant") as app:
        gr.Markdown(f"## Farmer Advisory Assistant\nCrop, irrigation and fertilizer questions in "
                    f"Tamil, Hindi or English.  \n_{DISCLAIMER}_")
        results = gr.State([])
        with gr.Row():
            with gr.Column(scale=3):
                lang = gr.Dropdown(list(LANGS), value="Auto-detect", label="Language")
                chat = gr.Chatbot(label="Chat", height=480)
                box = gr.Textbox(placeholder="Ask a question / கேள்வி கேளுங்கள் / प्रश्न पूछें",
                                 label="Question")
                send = gr.Button("Ask", variant="primary")
            with gr.Column(scale=2):
                src = gr.Markdown("_Sources appear here._", label="Sources")
        for trigger in (box.submit, send.click):
            trigger(respond, [box, chat, lang, results], [chat, box, src, results])
        chat.like(feedback, [results], None)
    return app


def main() -> None:
    """Load models once and launch on the host/port in config.yaml (app section).

    ``--open`` opens the app in the default browser once it is ready.
    """
    import argparse

    from src.agent.pipeline import Assistant

    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="open the app in the browser when ready")
    open_browser = ap.parse_args().open
    app_cfg = load_config()["app"]
    print("Loading models (about 30 seconds)...", flush=True)
    build_app(Assistant()).launch(server_name=app_cfg["host"], server_port=app_cfg["port"],
                                  inbrowser=open_browser)


if __name__ == "__main__":
    main()
