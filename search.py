"""Step 4: search the episodes.

Usage:
    python search.py "اليمن البحر الأحمر"
    python search.py "Iran nuclear talks"
"""
import sys

import chromadb
from sentence_transformers import SentenceTransformer

import config

TOP_K = 5
PREVIEW_CHARS = 300


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python search.py "your query"')
    query = " ".join(sys.argv[1:])

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    collection = client.get_collection(config.COLLECTION_NAME)

    # The query must be embedded with the same model used for the chunks.
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    query_embedding = model.encode([query], normalize_embeddings=True)

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=TOP_K,
    )

    # Chroma returns one list per query; we only sent one query, so take [0].
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for rank, (text, meta, distance) in enumerate(zip(documents, metadatas, distances), start=1):
        minutes, seconds = divmod(meta["start_seconds"], 60)
        print(f"\n#{rank}  {meta['title']}  ({meta['upload_date']})")
        print(f"    {meta['link']}  [{minutes}:{seconds:02d}]")
        print(f"    similarity: {1 - distance:.3f}")
        print(f"    {text[:PREVIEW_CHARS]}...")


if __name__ == "__main__":
    main()
