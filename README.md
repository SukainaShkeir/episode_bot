# Episode Bot: Phase 1 (ingestion + search)

Finds which past Arabic podcast episodes relate to a topic.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your playlist URL in .env
```

## Run, in order

```bash
python download.py   # captions + metadata  -> data/raw/
python process.py    # optional: preview how episodes get chunked
python ingest.py     # embed + store        -> data/chroma/  (re-runnable)
python search.py "اليمن البحر الأحمر"
```

## Files

| File | Job |
|---|---|
| `config.py` | paths and settings in one place |
| `download.py` | yt-dlp: Arabic auto-captions + metadata |
| `process.py` | clean rolling captions, split into ~2.5 min timestamped chunks |
| `ingest.py` | BGE-M3 embeddings into Chroma, skips episodes already stored |
| `search.py` | query the DB, print the top 5 chunks with `&t=` links |

## Re-chunking

Already-ingested episodes are skipped. If you change `CHUNK_SECONDS` or the
cleaning logic, delete `data/chroma/` and run `ingest.py` again.
