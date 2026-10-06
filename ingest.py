"""Step 3: embed every episode's chunks and store them in a local Chroma database.

Safe to re-run: episodes that are already in the database are skipped.
"""
import json

import chromadb
from sentence_transformers import SentenceTransformer

import config
from process import make_chunks


def already_ingested(collection, video_id):
    """True if the database already holds at least one chunk of this episode."""
    found = collection.get(where={"video_id": video_id}, limit=1)
    return len(found["ids"]) > 0


def ingest_episode(collection, model, metadata):
    """Chunk, embed and store one episode."""
    video_id = metadata["video_id"]
    vtt_path = config.RAW_DIR / f"{video_id}.{config.CAPTION_LANG}.vtt"
    chunks = make_chunks(vtt_path)
    if not chunks:
        print("  no text found, skipping")
        return

    texts = [chunk["text"] for chunk in chunks]
    # normalize_embeddings=True makes cosine similarity work properly
    embeddings = model.encode(texts, batch_size=8, normalize_embeddings=True)

    collection.add(
        ids=[f"{video_id}_{i}" for i in range(len(chunks))],
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[
            {
                "video_id": video_id,
                "title": metadata["title"],
                "upload_date": metadata["upload_date"],
                "start_seconds": chunk["start_seconds"],
                "link": f"{metadata['url']}&t={chunk['start_seconds']}",
            }
            for chunk in chunks
        ],
    )
    print(f"  stored {len(chunks)} chunks")


def main():
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # compare embeddings by cosine distance
    )

    # Find the episodes that still need ingesting
    pending = []
    for json_path in sorted(config.RAW_DIR.glob("*.json")):
        metadata = json.loads(json_path.read_text(encoding="utf-8"))
        if already_ingested(collection, metadata["video_id"]):
            print(f"{metadata['video_id']}: already ingested")
        else:
            pending.append(metadata)

    if not pending:
        print("Nothing new to ingest.")
        return

    # Loading the model is slow, so we only do it when there is work to do.
    print(f"Loading {config.EMBEDDING_MODEL} (the first run downloads ~2 GB)...")
    model = SentenceTransformer(config.EMBEDDING_MODEL)

    for number, metadata in enumerate(pending, start=1):
        print(f"[{number}/{len(pending)}] {metadata['video_id']}: {metadata['title']}")
        ingest_episode(collection, model, metadata)

    print(f"Done. The database now holds {collection.count()} chunks.")


if __name__ == "__main__":
    main()
