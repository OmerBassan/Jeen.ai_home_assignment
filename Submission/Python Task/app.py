import argparse
import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise SystemExit("Missing OPENAI_API_KEY. Add it to your .env file.")

client = OpenAI(api_key=API_KEY)

STORE_PATH = Path("store.json")
EMBED_MODEL = "text-embedding-3-small"


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError(f"Unsupported file format: {suffix}. Use .txt or .pdf.")


def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def embed(text: str) -> list[float]:
    response = client.embeddings.create(
        input=[text.replace("\n", " ")],
        model=EMBED_MODEL,
    )
    return response.data[0].embedding


def load_store() -> dict:
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    return {"chunks": [], "embeddings": [], "sources": []}


def save_store(store: dict) -> None:
    STORE_PATH.write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")


def cmd_ingest(file_path: str) -> None:
    if not Path(file_path).exists():
        raise SystemExit(f"File not found: {file_path}")

    print(f"Reading {file_path}...")
    text = extract_text(file_path)

    chunks = split_into_chunks(text)
    if not chunks:
        raise SystemExit("No text extracted from the file.")
    print(f"Split into {len(chunks)} chunks. Generating embeddings...")

    embeddings = [embed(chunk) for chunk in chunks]

    store = load_store()
    store["chunks"].extend(chunks)
    store["embeddings"].extend(embeddings)
    store["sources"].extend([file_path] * len(chunks))
    save_store(store)

    print(f"Done. Store now contains {len(store['chunks'])} chunks total.")


def cmd_search(query: str, top_k: int) -> None:
    store = load_store()
    if not store["chunks"]:
        raise SystemExit("Store is empty. Run: python app.py ingest <file>")

    query_embedding = np.array(embed(query)).reshape(1, -1)
    db_embeddings = np.array(store["embeddings"])

    scores = cosine_similarity(query_embedding, db_embeddings)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]

    print(f"\nQuery: {query}\n")
    for rank, idx in enumerate(top_indices, start=1):
        print(f"--- Result {rank}  (score: {scores[idx]:.4f}) ---")
        print(f"Source: {store['sources'][idx]}")
        print(f"{store['chunks'][idx]}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simple semantic search over TXT and PDF files using OpenAI embeddings."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a TXT or PDF file into the local store.")
    ingest_parser.add_argument("file", help="Path to a .txt or .pdf file")

    search_parser = subparsers.add_parser("search", help="Search the store for the most relevant chunks.")
    search_parser.add_argument("query", help="Your question")
    search_parser.add_argument("--top-k", type=int, default=3, help="Number of results to return (default: 3)")

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args.file)
    elif args.command == "search":
        cmd_search(args.query, top_k=args.top_k)


if __name__ == "__main__":
    main()
