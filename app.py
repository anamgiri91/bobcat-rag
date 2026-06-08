"""
app.py
======
Gradio interface for the Bobcat RAG — TXST Professor Advisor.
"""

import argparse
import gradio as gr
from generate import answer_question


DEFAULT_DB_PATH = "data/chroma_db"
DEFAULT_TOP_K   = 5

SOURCE_OPTIONS = {
    "All sources":       None,
    "RateMyProfessors":  "rmp",
    "Coursicle":         "coursicle",
    "Reddit r/txstate":  "reddit",
    "Official catalog":  "official",
}

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

:root {
    --maroon:       #4a1942;
    --maroon-light: #6b2760;
    --gold:         #c9a227;
    --gold-light:   #e8c547;
    --cream:        #faf8f3;
    --ink:          #1a1520;
    --muted:        #6b6070;
    --surface:      #ffffff;
    --border:       #e8e2ef;
    --shadow:       rgba(74, 25, 66, 0.12);
}

body, .gradio-container {
    background: var(--cream) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--ink) !important;
}

.gradio-container {
    max-width: 900px !important;
    margin: 0 auto !important;
    padding: 0 !important;
}

#hero-header {
    background: linear-gradient(135deg, var(--maroon) 0%, var(--maroon-light) 60%, #8b3a7e 100%);
    padding: 44px 48px 40px;
    border-radius: 0 0 32px 32px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}

#hero-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: rgba(201, 162, 39, 0.15);
}

.hero-logo-row {
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 14px;
}

.hero-title {
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    line-height: 1.1 !important;
    letter-spacing: -0.02em !important;
    margin: 0 !important;
}

.hero-title span { color: #e8c547; }

.hero-subtitle {
    font-size: 0.95rem !important;
    color: rgba(255,255,255,0.75) !important;
    margin: 0 !important;
    line-height: 1.5 !important;
}

.hero-badges { display: flex; gap: 8px; margin-top: 18px; flex-wrap: wrap; }

.hero-badge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.9);
    font-size: 0.75rem;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 100px;
}

#main-content { padding: 0 24px 48px; }

#question-input textarea {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    border: 2px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 16px !important;
    background: var(--surface) !important;
    color: var(--ink) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    box-shadow: 0 2px 8px var(--shadow) !important;
}

#question-input textarea:focus {
    border-color: var(--maroon) !important;
    box-shadow: 0 0 0 3px rgba(74,25,66,0.08), 0 2px 8px var(--shadow) !important;
    outline: none !important;
}

#question-input label, #source-filter label {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin-bottom: 8px !important;
}

#ask-btn {
    background: linear-gradient(135deg, var(--maroon), var(--maroon-light)) !important;
    color: white !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.03em !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 32px !important;
    cursor: pointer !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
    box-shadow: 0 4px 16px rgba(74,25,66,0.35) !important;
    width: 100% !important;
}

#ask-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(74,25,66,0.45) !important;
}

#answer-box, #sources-box {
    background: var(--surface) !important;
    border: 2px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 12px var(--shadow) !important;
    overflow: hidden !important;
}

#answer-box textarea, #sources-box textarea {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.65 !important;
    color: var(--ink) !important;
    background: transparent !important;
    border: none !important;
    padding: 20px !important;
}

#answer-box label {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--maroon) !important;
    padding: 14px 20px 0 !important;
    display: block !important;
}

#sources-box label {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--gold) !important;
    padding: 14px 20px 0 !important;
    display: block !important;
}

.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 28px 0;
}

.examples-header {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--muted) !important;
    margin-bottom: 10px !important;
}

#footer-text {
    text-align: center;
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 32px;
    font-style: italic;
}
"""

LOGO_SVG = """
<svg width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="26" cy="26" r="25" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
  <circle cx="26" cy="26" r="22" fill="rgba(255,255,255,0.1)"/>
  <ellipse cx="26" cy="27" rx="12" ry="11" fill="rgba(255,255,255,0.95)"/>
  <path d="M16 20 L13 13 L20 17 Z" fill="rgba(255,255,255,0.95)"/>
  <path d="M36 20 L39 13 L32 17 Z" fill="rgba(255,255,255,0.95)"/>
  <path d="M16 19 L14.5 14.5 L18.5 17.5 Z" fill="#c9a227"/>
  <path d="M36 19 L37.5 14.5 L33.5 17.5 Z" fill="#c9a227"/>
  <circle cx="21" cy="25" r="2.5" fill="#4a1942"/>
  <circle cx="31" cy="25" r="2.5" fill="#4a1942"/>
  <circle cx="21.8" cy="24.2" r="0.8" fill="white"/>
  <circle cx="31.8" cy="24.2" r="0.8" fill="white"/>
  <path d="M24.5 29 Q26 31 27.5 29 Q26 28 24.5 29 Z" fill="#c9a227"/>
  <circle cx="19" cy="28" r="0.7" fill="#4a1942" opacity="0.5"/>
  <circle cx="17" cy="29.5" r="0.7" fill="#4a1942" opacity="0.5"/>
  <circle cx="33" cy="28" r="0.7" fill="#4a1942" opacity="0.5"/>
  <circle cx="35" cy="29.5" r="0.7" fill="#4a1942" opacity="0.5"/>
  <path d="M26 6 L27.2 9.6 L31 9.6 L28 11.8 L29.2 15.4 L26 13.2 L22.8 15.4 L24 11.8 L21 9.6 L24.8 9.6 Z" fill="#c9a227"/>
</svg>
"""

HERO_HTML = f"""
<div id="hero-header">
  <div class="hero-logo-row">
    {LOGO_SVG}
    <div>
      <div class="hero-title">Bobcat <span>Advisor</span></div>
    </div>
  </div>
  <p class="hero-subtitle">Ask anything about TXST CS professors — exams, workload, grading, and which section to take.</p>
  <div class="hero-badges">
    <span class="hero-badge">📚 RateMyProfessors</span>
    <span class="hero-badge">🎓 Coursicle</span>
    <span class="hero-badge">💬 Reddit r/txstate</span>
    <span class="hero-badge">📋 TXST Catalog</span>
  </div>
</div>
"""


def handle_question(
    question:     str,
    source_label: str = "All sources",
    db_path:      str = DEFAULT_DB_PATH,
    top_k:        int = DEFAULT_TOP_K,
) -> tuple[str, str]:
    question = question.strip()
    if not question:
        return "Please enter a question.", "—"

    source_filter = SOURCE_OPTIONS.get(source_label)

    try:
        answer, sources = answer_question(
            query         = question,
            db_path       = db_path,
            top_k         = top_k,
            source_filter = source_filter,
        )
        return answer, sources
    except EnvironmentError as e:
        return str(e), "—"
    except Exception as e:
        return f"Something went wrong: {e}", "—"


def build_ui(db_path: str = DEFAULT_DB_PATH) -> gr.Blocks:
    with gr.Blocks(
        title = "Bobcat Advisor — TXST CS",
        theme = gr.themes.Base(),
        css   = CUSTOM_CSS,
    ) as demo:

        gr.HTML(HERO_HTML)

        with gr.Column(elem_id="main-content"):

            question = gr.Textbox(
                label       = "Your question",
                placeholder = (
                    "e.g.  What do students say about Burtscher's workload?\n"
                    "      How do Seaman and Gholoom compare for CS1428?\n"
                    "      Is Lee Koh's Assembly course hard?"
                ),
                lines   = 3,
                elem_id = "question-input",
            )

            source_dropdown = gr.Dropdown(
                choices = list(SOURCE_OPTIONS.keys()),
                value   = "All sources",
                label   = "Filter by source",
                elem_id = "source-filter",
            )

            ask_btn = gr.Button("Ask Bobcat →", variant="primary", elem_id="ask-btn")

            gr.HTML('<div class="section-divider"></div>')

            with gr.Row():
                answer = gr.Textbox(
                    label       = "Answer",
                    lines       = 10,
                    interactive = False,
                    elem_id     = "answer-box",
                )
                sources = gr.Textbox(
                    label       = "Sources",
                    lines       = 10,
                    interactive = False,
                    elem_id     = "sources-box",
                )

            gr.HTML('<div class="section-divider"></div>')
            gr.HTML('<p class="examples-header">Try one of these</p>')

            gr.Examples(
                examples = [
                    ["What do students say about Martin Burtscher's workload?"],
                    ["Does Husain Gholoom curve exam grades?"],
                    ["Is Lee Koh's Assembly course worth taking?"],
                    ["How do Jill Seaman and Gholoom compare for CS1428?"],
                    ["Which professor is best for CS4328 Operating Systems?"],
                    ["How hard is Keshav Bhandari's CS2308 class?"],
                    ["What do students say about Mina Guirguis's teaching style?"],
                    ["Are Ted Lehr's lectures useful for CS3354?"],
                ],
                inputs = question,
            )

            gr.HTML('<p id="footer-text">Answers grounded in real student reviews · Not affiliated with Texas State University</p>')

        ask_btn.click(
            fn      = lambda q, s: handle_question(q, s, db_path=db_path),
            inputs  = [question, source_dropdown],
            outputs = [answer, sources],
        )

        question.submit(
            fn      = lambda q, s: handle_question(q, s, db_path=db_path),
            inputs  = [question, source_dropdown],
            outputs = [answer, sources],
        )

    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Bobcat Advisor")
    parser.add_argument("--db",    default=DEFAULT_DB_PATH)
    parser.add_argument("--port",  type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    demo = build_ui(db_path=args.db)
    demo.launch(server_name="0.0.0.0", server_port=args.port, share=args.share)