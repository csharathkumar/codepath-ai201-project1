"""
app.py — Milestone 5: Gradio Interface

Run with:
    python app.py

Then open http://localhost:7860 in your browser.
"""

import gradio as gr
from generate import ask


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", ""

    result = ask(question)

    sources_text = "\n".join(f"• {s}" for s in result["sources"]) if result["sources"] else "No sources retrieved."
    return result["answer"], sources_text


# ── UI Layout ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Rutgers CS Unofficial Guide") as demo:
    gr.Markdown(
        """
        # 📚 Rutgers CS Unofficial Guide
        Ask questions about CS courses and professors — answers come from real student reviews,
        Reddit threads, and community guides. Not from the official course catalog.
        """
    )

    with gr.Row():
        with gr.Column(scale=2):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. What do students say about CS213? Is CS336 worth taking?",
                lines=2,
            )
            ask_btn = gr.Button("Ask", variant="primary")

        with gr.Column(scale=3):
            answer_box = gr.Textbox(
                label="Answer",
                lines=8,
                interactive=False,
            )
            sources_box = gr.Textbox(
                label="Sources",
                lines=3,
                interactive=False,
            )

    gr.Examples(
        examples=[
            ["What do students say about CS213 Systems Programming?"],
            ["Which CS professors at Rutgers are known for being good teachers?"],
            ["How hard is CS112 Data Structures?"],
            ["Is CS336 Databases worth taking?"],
            ["What are the easiest CS electives at Rutgers?"],
        ],
        inputs=question_box,
    )

    ask_btn.click(handle_query, inputs=question_box, outputs=[answer_box, sources_box])
    question_box.submit(handle_query, inputs=question_box, outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch()
