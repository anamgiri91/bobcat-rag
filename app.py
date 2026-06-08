"""
app.py
======
Gradio interface for the Bobcat RAG — TXST Professor Advisor.

Wires together:
  retrieve.py  →  generate.py  →  Gradio UI

Run with:
    python app.py
    python app.py --db data/chroma_db --port 7860

Make sure you have embedded your chunks first:
    python embed.py --chunks data/chunks.jsonl --db data/chroma_db

Environment:
    export ANTHROPIC_API_KEY=your_key_here

Dependencies:
    pip install gradio anthropic chromadb sentence-transformers
"""

import argparse
import gradio as gr
from generate import answer_question


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_DB_PATH = "data/chroma_db"
DEFAULT_TOP_K   = 5
APP_TITLE       = "🤠 TXST Professor Advisor"
APP_DESCRIPTION = """Ask anything about Texas State CS professors and courses.
Answers are grounded in real student reviews from RateMyProfessors, Coursicle,
Reddit r/txstate, and the official TXST course catalog.
**No hallucinations — every answer cites its sources.**"""


# ---------------------------------------------------------------------------
# Handler function  (called by Gradio on every button click)
# ---------------------------------------------------------------------------

def handle_question(
    question: str,
    db_path:  str = DEFAULT_DB_PATH,
    top_k:    int = DEFAULT_TOP_K,
) -> tuple[str, str]:
    """
    Gradio event handler.

    Validates input, calls answer_question(), and returns
    (answer, sources) for display in the two output textboxes.

    Empty or whitespace-only questions are caught here before
    touching the database or the API.
    """
    question = question.strip()
    if not question:
        return (
            "Please enter a question.",
            "—"
        )

    try:
        answer, sources = answer_question(
            query   = question,
            db_path = db_path,
            top_k   = top_k,
        )
        return answer, sources

    except EnvironmentError as e:
        # ANTHROPIC_API_KEY not set
        return str(e), "—"

    except Exception as e:
        return f"Something went wrong: {e}", "—"


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def build_ui(db_path: str = DEFAULT_DB_PATH) -> gr.Blocks:
    """
    Build and return the Gradio Blocks interface.

    Layout:
      ┌─────────────────────────────────┐
      │  🤠 TXST Professor Advisor       │
      │  [description]                  │
      ├─────────────────────────────────┤
      │  Question textbox               │
      │  [Ask] button                   │
      ├─────────────────────────────────┤
      │  Answer textbox   (8 lines)     │
      │  Sources textbox  (5 lines)     │
      └─────────────────────────────────┘
    """
    with gr.Blocks(
        title = APP_TITLE,
        theme = gr.themes.Soft(),
    ) as demo:

        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown(APP_DESCRIPTION)

        with gr.Row():
            with gr.Column(scale=3):
                question = gr.Textbox(
                    label       = "Ask about a professor or course",
                    placeholder = (
                        "e.g. What do students say about Martin Burtscher's workload?\n"
                        "     Is Lee Koh's Assembly course hard?\n"
                        "     Does Mina Guirguis curve grades?"
                    ),
                    lines = 3,
                )
                ask_btn = gr.Button("Ask", variant="primary")

        with gr.Row():
            with gr.Column():
                answer = gr.Textbox(
                    label    = "Answer",
                    lines    = 8,
                    interactive = False,
                )
            with gr.Column():
                sources = gr.Textbox(
                    label    = "Sources",
                    lines    = 8,
                    interactive = False,
                )

        # Example questions so students know what to ask
        gr.Examples(
            examples = [
                ["What do students say about Martin Burtscher's workload?"],
                ["Does Husain Gholoom curve exam grades?"],
                ["Is Lee Koh's Assembly course worth taking?"],
                ["What is the difference between CS 3358 and CS 3354?"],
                ["Which professor is best for CS 4328 Operating Systems?"],
                ["How hard is Keshav Bhandari's CS 2308 class?"],
                ["What do students say about Mina Guirguis's teaching style?"],
                ["Are Ted Lehr's lectures useful for CS 3354?"],
            ],
            inputs = question,
        )

        # Wire the button to the handler
        ask_btn.click(
            fn      = lambda q: handle_question(q, db_path=db_path),
            inputs  = [question],
            outputs = [answer, sources],
        )

        # Also trigger on Enter key in the textbox
        question.submit(
            fn      = lambda q: handle_question(q, db_path=db_path),
            inputs  = [question],
            outputs = [answer, sources],
        )

    return demo


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the TXST Professor Advisor")
    parser.add_argument(
        "--db", default=DEFAULT_DB_PATH,
        help=f"ChromaDB directory (default: {DEFAULT_DB_PATH})"
    )
    parser.add_argument(
        "--port", type=int, default=7860,
        help="Port to serve on (default: 7860)"
    )
    parser.add_argument(
        "--share", action="store_true",
        help="Generate a public Gradio share link"
    )
    args = parser.parse_args()

    demo = build_ui(db_path=args.db)
    demo.launch(
        server_port = args.port,
        share       = args.share,
    )