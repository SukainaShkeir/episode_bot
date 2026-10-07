"""Step 4: search the episodes.

Usage:
    python search.py "اليمن البحر الأحمر"
    python search.py "Iran nuclear talks"

Results are printed and also saved to results.html (open it in a browser or VS Code:
Arabic shows correctly there and the links are clickable).
"""
import html
import sys

import chromadb
from sentence_transformers import SentenceTransformer

import config

TOP_K = 5
PREVIEW_CHARS = 300
HTML_FILE = "results.html"


def save_html(query, results):
    """Write the results to an HTML file, which displays Arabic properly."""
    parts = [
        '<meta charset="utf-8">',
        '<body dir="rtl" style="font-family: sans-serif; max-width: 800px; margin: auto">',
        f"<h2>{html.escape(query)}</h2>",
    ]
    for rank, (text, meta, distance) in enumerate(results, start=1):
        minutes, seconds = divmod(meta["start_seconds"], 60)
        parts.append(f"<h3>#{rank} {html.escape(meta['title'])} ({meta['upload_date']})</h3>")
        parts.append(
            f'<p><a href="{html.escape(meta["link"])}">{minutes}:{seconds:02d}</a>'
            f" &middot; similarity {1 - distance:.3f}</p>"
        )
        parts.append(f"<p>{html.escape(text)}</p>")
    with open(HTML_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(parts))


def main():
    # When output is redirected to a file (> results.txt), Windows would use an
    # encoding without Arabic letters. Force UTF-8 in that case.
    if not sys.stdout.isatty():
        sys.stdout.reconfigure(encoding="utf-8")

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

    results = list(zip(documents, metadatas, distances))
    save_html(query, results)

    for rank, (text, meta, distance) in enumerate(results, start=1):
        minutes, seconds = divmod(meta["start_seconds"], 60)
        print(f"\n#{rank}  {meta['title']}  ({meta['upload_date']})")
        print(f"    {meta['link']}  [{minutes}:{seconds:02d}]")
        print(f"    similarity: {1 - distance:.3f}")
        print(f"    {text[:PREVIEW_CHARS]}...")

    print(f"\nSaved to {HTML_FILE}")


if __name__ == "__main__":
    main()
