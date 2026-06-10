"""
generate.py — Milestone 5: Grounded Generation

Retrieves relevant chunks for a question and generates a grounded answer
using Groq's LLM. Answers are restricted to retrieved context only.
Source attribution is added programmatically — not left to the LLM.

Usage:
    python generate.py "What do students say about CS213?"
"""

import os
import sys
from groq import Groq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

from embed import EMBEDDING_MODEL, COLLECTION_NAME, CHROMA_DIR, TOP_K, retrieve

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

GROQ_MODEL = "llama-3.3-70b-versatile"

# Grounding system prompt — instructs model to answer ONLY from context.
# Uses explicit refusal instruction so it can't fall back on training data.
SYSTEM_PROMPT = """You are a helpful assistant for students at Rutgers University \
looking for honest, peer-sourced information about CS courses and professors.

STRICT RULES — you must follow these exactly:
1. Answer ONLY using information from the CONTEXT section provided below.
2. Do NOT use any knowledge from your training data about Rutgers, professors, or courses.
3. Do NOT make up or infer opinions, ratings, or facts not present in the context.
4. If the context contains partial information, use it and note that coverage is limited.
5. Only say "I don't have enough information on that in my documents." if the context \
contains zero relevant information about the topic.
6. Keep your answer concise and specific — quote or closely paraphrase the source material.
7. Do not add a sources section — sources will be appended separately."""


def build_context(hits: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    lines = ["CONTEXT:"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"[{i}] (from {hit['source']})\n{hit['text']}")
    return "\n\n".join(lines)


# ── Main ask function ─────────────────────────────────────────────────────────

def ask(question: str, k: int = TOP_K) -> dict:
    """
    End-to-end: retrieve → generate → return grounded answer with sources.

    Returns:
        {
            "answer":  str,           # LLM response, grounded to context
            "sources": list[str],     # source filenames (programmatic, not LLM-generated)
            "chunks":  list[dict],    # raw retrieved chunks for inspection
        }
    """
    # 1. Load model + collection
    model      = SentenceTransformer(EMBEDDING_MODEL)
    client     = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    # 2. Retrieve top-k chunks
    hits = retrieve(question, collection, model, k=k)

    # Filter out very weak matches (distance > 0.85) — don't send noise to the LLM
    strong_hits = [h for h in hits if h["distance"] < 0.85]
    if not strong_hits:
        return {
            "answer":  "I don't have enough information on that in my documents.",
            "sources": [],
            "chunks":  hits,
        }

    # 3. Build context block
    context = build_context(strong_hits)

    # 4. Call Groq
    client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client_groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"{context}\n\nQUESTION: {question}"},
        ],
        temperature=0.2,   # low temperature = more faithful to context, less hallucination
        max_tokens=512,
    )
    answer = response.choices[0].message.content.strip()

    # 5. Source attribution — programmatic, not LLM-generated
    # Deduplicate and clean up filenames for display
    seen = set()
    sources = []
    for h in strong_hits:
        src = h["source"].replace(".txt", "").replace("_", " ")
        if src not in seen:
            seen.add(src)
            sources.append(src)

    return {"answer": answer, "sources": sources, "chunks": strong_hits}


# ── CLI for quick testing ─────────────────────────────────────────────────────

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What do students say about CS213?"

    print(f"\nQuestion: {question}\n")
    result = ask(question)

    print("Answer:")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  • {s}")
    print()
