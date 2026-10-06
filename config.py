"""Shared settings for every script in the project."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Read the .env file and put its values into os.environ
load_dotenv()

# --- From .env ---
PLAYLIST_URL = os.getenv("PLAYLIST_URL")

# --- Folders (all generated, all inside data/) ---
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"        # captions (.vtt) and metadata (.json)
CHROMA_DIR = DATA_DIR / "chroma"  # the vector database

# --- Captions ---
CAPTION_LANG = "ar"

# --- Chunking ---
CHUNK_SECONDS = 150   # ~2.5 minutes per chunk
OVERLAP_LINES = 2     # caption lines repeated at the start of the next chunk

# --- Embeddings / vector DB ---
EMBEDDING_MODEL = "BAAI/bge-m3"
COLLECTION_NAME = "episodes"
