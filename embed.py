"""
embed.py — Milestone 4: Embed Chunks and Test Retrieval

Embeds all chunks from ingest.py using all-MiniLM-L6-v2,
stores them in a persistent ChromaDB collection with source metadata,
and tests retrieval with evaluation queries.

Usage:
    python embed.py              # embed all chunks + run test queries
    python embed.py --query "your question here"  # query only (no re-embed)
"""

import os
import sys
import argparse
import chromadb
from sentence_transformers import SentenceTransformer
from ingest import build_chunks, DOCUMENTS_DIR

# ── Config ────────────────────────────────────────────────────────────────────

EMBEDDING_MODEL  = "all-MiniLM-L6-v2"
COLLECTION_NAME  = "rutgers_cs_guide"
CHROMA_DIR       = os.path.join(os.path.dirname(__file__), ".chromadb")
TOP_K            = 5

# Test queries from planning.md evaluation plan
TEST_QUERIES = [
    "What do students say about CS213 Systems Programming?",
    "Which CS professors at Rutgers are known for being good teachers?",
    "How hard is CS112 Data Structures?",
]


# ── Setup ─────────────────────────────────────────────────────────────────────

def get_collection(reset: bool = False):
    """Return a persistent ChromaDB collection (cosine similarity)."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  Deleted existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # cosine distance; lower = more similar
    )
    return collection


# ── Embed + Store ─────────────────────────────────────────────────────────────

def embed_and_store(chunks: list[dict], collection) -> None:
    """
    Embed each chunk with all-MiniLM-L6-v2 and upsert into ChromaDB.
    Stores source filename and chunk position as metadata.
    """
    print(f"\n── Loading embedding model: {EMBEDDING_MODEL} ───────────────")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"── Embedding {len(chunks)} chunks ───────────────────────────")
    texts     = [c["text"]   for c in chunks]
    ids       = [c["id"]     for c in chunks]
    metadatas = [{"source": c["source"]} for c in chunks]

    # Embed in one batch (sentence-transformers handles batching internally)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_list=True)

    print("── Storing in ChromaDB ───────────────────────────────────")
    collection.upsert(
        ids        = ids,
        embeddings = embeddings,
        documents  = texts,
        metadatas  = metadatas,
    )
    print(f"  ✓  {collection.count()} chunks stored in '{COLLECTION_NAME}'")


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, collection, model: SentenceTransformer, k: int = TOP_K) -> list[dict]:
    """
    Embed the query and return the top-k most similar chunks.
    Each result: {"text", "source", "distance"}
    Distance is cosine distance (0 = identical, 1 = unrelated, 2 = opposite).
    Scores below 0.5 are strong matches; above 0.7 is weak.
    """
    query_embedding = model.encode(query, convert_to_list=True)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({"text": doc, "source": meta["source"], "distance": dist})
    return hits


def print_results(query: str, hits: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"  QUERY: {query}")
    print(f"{'='*60}")
    for i, hit in enumerate(hits, 1):
        quality = "✓ strong" if hit["distance"] < 0.4 else ("~ ok" if hit["distance"] < 0.6 else "✗ weak")
        print(f"\n  [{i}] distance={hit['distance']:.3f}  {quality}  |  {hit['source']}")
        print(f"  {hit['text'][:300]}{'...' if len(hit['text']) > 300 else ''}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, help="Run a single retrieval query")
    parser.add_argument("--no-embed", action="store_true", help="Skip embedding, just query existing collection")
    args = parser.parse_args()

    collection = get_collection(reset=not args.no_embed)

    if not args.no_embed:
        print("\n── Building chunks from documents/ ──────────────────────")
        chunks = build_chunks(DOCUMENTS_DIR)
        if not chunks:
            print("  ✗  No chunks found. Did you run fetch_documents.py and ingest.py first?")
            sys.exit(1)
        embed_and_store(chunks, collection)

    print(f"\n── Loading model for queries ─────────────────────────────")
    model = SentenceTransformer(EMBEDDING_MODEL)

    queries = [args.query] if args.query else TEST_QUERIES
    print(f"\n── Running {len(queries)} test queries ──────────────────────────")
    for query in queries:
        hits = retrieve(query, collection, model)
        print_results(query, hits)

    print(f"\n{'='*60}")
    print("  Retrieval test complete.")
    print("  Check distance scores — aim for top results below 0.5.")
    print("  If scores are high (>0.6) or results are off-topic, see README for debug tips.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
