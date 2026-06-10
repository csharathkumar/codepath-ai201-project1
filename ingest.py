"""
ingest.py — Milestone 3: Document Pipeline
Loads .txt files from documents/, cleans them, and splits into chunks.

Usage:
    python ingest.py
"""

import os
import re
import random
import html


# ── Config (matches planning.md) ─────────────────────────────────────────────

DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "documents")
CHUNK_SIZE    = 400   # characters
OVERLAP       = 50    # characters


# ── Stage 1: Load ─────────────────────────────────────────────────────────────

def load_documents(folder: str) -> list[dict]:
    """
    Load every .txt file in folder.
    Returns a list of {"source": filename, "text": raw_text}.
    """
    docs = []
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(folder, filename)
        if os.path.isdir(path):
            print(f"  Skipped {filename}  (is a directory, not a file)")
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        docs.append({"source": filename, "text": raw})
        print(f"  Loaded  {filename}  ({len(raw):,} chars)")
    return docs


# ── Stage 2: Clean ────────────────────────────────────────────────────────────

def strip_rtf(text: str) -> str:
    """Strip RTF formatting codes and return plain text."""
    # Remove RTF control words (e.g. \pard, \fs28, \cb1)
    text = re.sub(r"\\[a-z]+[-]?\d*\s?", " ", text)
    # Remove RTF control symbols (e.g. \*, \~)
    text = re.sub(r"\\.", " ", text)
    # Remove curly braces (RTF grouping)
    text = re.sub(r"[{}]", " ", text)
    # Decode RTF unicode escapes: 舲 → ignore (line separator), 舦 → bullet
    text = re.sub(r"\\u\d+\s?", " ", text)
    return text


def clean_text(text: str) -> str:
    """
    Remove RTF codes, HTML tags, HTML entities, and boilerplate noise.
    Keep substantive content: reviews, opinions, course descriptions.
    """
    # 0. Strip RTF if present (TextEdit saves .txt as RTF on Mac)
    if text.lstrip().startswith("{\\rtf") or "\\pard" in text[:500]:
        text = strip_rtf(text)

    # 1. Strip HTML tags (catches any leftover from scraping)
    text = re.sub(r"<[^>]+>", " ", text)

    # 2. Decode HTML entities (&amp; &nbsp; &#39; etc.)
    text = html.unescape(text)

    # 3. Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # 4. Remove Reddit/forum artifacts: vote counts, share buttons, timestamps
    text = re.sub(r"\b\d+\s*(points?|comments?|votes?|upvotes?|hours? ago|days? ago|months? ago)\b", "", text, flags=re.IGNORECASE)

    # 5. Remove lines that are pure boilerplate (nav, buttons, short noise)
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Skip very short lines that are likely UI artifacts
        if len(line) < 5:
            continue
        # Skip common boilerplate phrases
        boilerplate = [
            "log in", "sign up", "sign in", "cookie", "privacy policy",
            "terms of service", "read more", "show more", "load more",
            "share", "save", "hide", "report", "permalink", "embed",
            "advertisement", "sponsored", "click here", "subscribe",
            "follow us", "all rights reserved", "javascript",
        ]
        if any(bp in line.lower() for bp in boilerplate):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # 6. Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


# ── Stage 3: Chunk ────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Split text into overlapping fixed-size character chunks.
    Skips empty or near-empty chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) > 20:   # filter out fragments that carry no meaning
            chunks.append(chunk)
        start += chunk_size - overlap   # step forward, leaving overlap behind
    return chunks


# ── Stage 4: Build chunk records ──────────────────────────────────────────────

def build_chunks(folder: str) -> list[dict]:
    """
    Full pipeline: load → clean → chunk.
    Returns a list of {"id", "source", "text"} dicts ready for embedding.
    """
    docs = load_documents(folder)
    all_chunks = []
    for doc in docs:
        cleaned = clean_text(doc["text"])
        chunks  = chunk_text(cleaned)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id":     f"{doc['source']}__chunk{i:04d}",
                "source": doc["source"],
                "text":   chunk,
            })
    return all_chunks


# ── Inspection helpers ────────────────────────────────────────────────────────

def inspect_chunks(chunks: list[dict], n: int = 5) -> None:
    """Print n random chunks so you can visually verify quality."""
    print(f"\n{'='*60}")
    print(f"  CHUNK INSPECTION — {n} random samples")
    print(f"{'='*60}")
    sample = random.sample(chunks, min(n, len(chunks)))
    for i, chunk in enumerate(sample, 1):
        print(f"\n── Chunk {i} (source: {chunk['source']}) ──")
        print(chunk["text"])
    print(f"\n{'='*60}")


def chunk_stats(chunks: list[dict]) -> None:
    """Print summary statistics about the chunk set."""
    lengths = [len(c["text"]) for c in chunks]
    sources = {}
    for c in chunks:
        sources[c["source"]] = sources.get(c["source"], 0) + 1

    print(f"\n── Chunk Stats ───────────────────────────────────────────")
    print(f"  Total chunks  : {len(chunks)}")
    print(f"  Avg length    : {sum(lengths)//len(lengths)} chars")
    print(f"  Min / Max     : {min(lengths)} / {max(lengths)} chars")
    print(f"\n  Chunks per source:")
    for src, count in sorted(sources.items()):
        print(f"    {src}: {count}")

    # Warn if outside healthy range
    if len(chunks) < 50:
        print("\n  ⚠  Fewer than 50 chunks — chunks may be too large or documents too small.")
    elif len(chunks) > 2000:
        print("\n  ⚠  More than 2,000 chunks — chunks may be too small, retrieval signal may be weak.")
    else:
        print(f"\n  ✓  Chunk count looks healthy (50–2000 range).")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n── Loading documents ─────────────────────────────────────")
    chunks = build_chunks(DOCUMENTS_DIR)

    chunk_stats(chunks)
    inspect_chunks(chunks, n=5)

    print("\nPipeline complete. Review the 5 chunks above before moving to Milestone 4.")
    print("If you see HTML artifacts, fragments, or boilerplate — fix clean_text() first.\n")
