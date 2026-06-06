"""
embed.py
========
Reads chunks.jsonl, embeds every chunk using all-MiniLM-L6-v2,
and stores the vectors in a persistent ChromaDB collection.

Run once before starting the app:
    python embed.py --chunks data/chunks.jsonl --db data/chroma_db

Re-running is safe: ChromaDB upserts by chunk ID, so duplicates
are overwritten rather than inserted twice.

EMBEDDING STRATEGY (Fix 1)
---------------------------
Each chunk's TEXT is stored in ChromaDB in full (header + review body),
but only the BODY is embedded as a vector.

Why: The header line contains pipe-delimited metadata like:
  "Professor: Jill Seaman | Course: CS 1428 | Source: Coursicle | ..."

When this is included in the embedding, the semantic vector is partially
about the metadata format rather than the review content. This weakens
cosine similarity matching — a query like "best professor for CS 1428"
fails to retrieve relevant chunks because the embedding space is polluted
by repeated header patterns that look similar across all chunks.

Embedding only the body text (the actual student opinion) makes the
vectors represent meaning rather than format, significantly improving
retrieval accuracy.

Dependencies:
    pip install chromadb sentence-transformers
"""

import json
import argparse
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COLLECTION_NAME = "txstate_cs_reviews"
EMBED_MODEL     = "all-MiniLM-L6-v2"
BATCH_SIZE      = 64          # how many chunks to embed + upsert at once


# ---------------------------------------------------------------------------
# Body extractor
# ---------------------------------------------------------------------------

def get_body(text: str) -> str:
    """
    Extract the review body from a chunk — everything after the first
    blank line (which separates the metadata header from the content).

    Example input:
      "Professor: Jill Seaman | Course: CS 1428 | ...\n\nShe is a fair
       grader and gives opportunities..."

    Returns:
      "She is a fair grader and gives opportunities..."

    For reddit and catalog chunks that have no header, the full text
    is returned unchanged since split("\n\n", 1) returns [text] with
    no second element.
    """
    parts = text.split("\n\n", 1)
    return parts[1].strip() if len(parts) > 1 else text.strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_index(chunks_path: Path, db_path: Path) -> None:
    print(f"Loading chunks from {chunks_path} ...")
    chunks = [json.loads(line) for line in chunks_path.open(encoding="utf-8")]
    print(f"  {len(chunks)} chunks loaded")

    print(f"\nLoading embedding model: {EMBED_MODEL} ...")
    model = SentenceTransformer(EMBED_MODEL)

    print(f"\nConnecting to ChromaDB at {db_path} ...")
    db_path.mkdir(parents=True, exist_ok=True)
    client     = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection(
        name     = COLLECTION_NAME,
        metadata = {"hnsw:space": "cosine"},   # cosine similarity for retrieval
    )

    print(f"\nEmbedding and upserting in batches of {BATCH_SIZE} ...")
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]

        # Store the FULL text (header + body) so the app can display it
        full_texts = [c["text"]     for c in batch]
        ids        = [c["id"]       for c in batch]
        metas      = [c["metadata"] for c in batch]

        # Embed ONLY the body — strips metadata header before vectorising.
        # This is Fix 1: body-only embedding for accurate retrieval.
        # See module docstring for full explanation.
        body_texts = [get_body(c["text"]) for c in batch]
        embeddings = model.encode(body_texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids        = ids,
            documents  = full_texts,   # full text stored for display
            embeddings = embeddings,   # body-only vector for similarity search
            metadatas  = metas,
        )

        done = min(i + BATCH_SIZE, len(chunks))
        print(f"  [{done:>4}/{len(chunks)}] upserted")

    print(f"\nDone. Collection '{COLLECTION_NAME}' has {collection.count()} documents.")
    print(f"\nNote: embeddings were generated from review bodies only (not headers).")
    print(f"      If you previously built an index with full-text embeddings,")
    print(f"      delete data/chroma_db/ and re-run this script to rebuild.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed chunks into ChromaDB")
    parser.add_argument("--chunks", default="data/chunks.jsonl",
                        help="Path to chunks.jsonl (default: data/chunks.jsonl)")
    parser.add_argument("--db", default="data/chroma_db",
                        help="ChromaDB persistence directory (default: data/chroma_db)")
    args = parser.parse_args()

    build_index(Path(args.chunks), Path(args.db))