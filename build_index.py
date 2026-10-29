"""Build a searchable vector index from prepared document chunks."""

import argparse
import hashlib
import json
from pathlib import Path

from openai import OpenAI

from onboarding.config import (
    ENDPOINT,
    EMBEDDING_MODEL,
    DEFAULT_CHUNK_SIZE,
    get_api_key,
)

ROOT = Path(__file__).resolve().parent
INDEX_FILE = ROOT / "artifacts" / "vector-index.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=DEFAULT_CHUNK_SIZE)
    args = parser.parse_args()

    if args.size <= 0:
        parser.error("--size must be positive.")

    chunks_file = ROOT / "artifacts" / f"chunks-{args.size}.jsonl"

    if not chunks_file.exists():
        raise SystemExit(
            f"Missing {chunks_file.name}. Run:\n"
            f"python -m onboarding prepare --size {args.size}"
        )

    source_bytes = chunks_file.read_bytes()
    chunks = [
        json.loads(line)
        for line in source_bytes.decode("utf-8-sig").splitlines()
        if line.strip()
    ]

    if not chunks:
        raise SystemExit("The chunks file is empty.")

    if any(not chunk.get("text", "").strip() for chunk in chunks):
        raise SystemExit("An empty chunk was found. Prepare documents again.")

    print(f"Loaded {len(chunks)} chunks.")
    print(f"Embedding deployment: {EMBEDDING_MODEL}")
    api_key = get_api_key()
    indexed_chunks = []
    batch_size = 16

    with OpenAI(
        base_url=ENDPOINT,
        api_key=api_key,
        timeout=60.0,
        max_retries=2,
    ) as client:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            print(
                f"Embedding chunks {start + 1}–"
                f"{start + len(batch)} of {len(chunks)}...",
                flush=True,
            )

            result = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=[chunk["text"] for chunk in batch],
                encoding_format="float",
            )

            embeddings = sorted(result.data, key=lambda item: item.index)

            if [item.index for item in embeddings] != list(range(len(batch))):
                raise RuntimeError("Azure returned unexpected embedding indexes.")

            for chunk, item in zip(batch, embeddings):
                indexed_chunks.append({
                    **chunk,
                    "embedding": item.embedding,
                })

    dimensions = len(indexed_chunks[0]["embedding"])

    if dimensions == 0 or any(
        len(chunk["embedding"]) != dimensions
        for chunk in indexed_chunks
    ):
        raise RuntimeError("Embedding dimensions are inconsistent.")

    index = {
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": args.size,
        "endpoint": ENDPOINT,
        "dimensions": dimensions,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "chunks": indexed_chunks,
    }

    # Keep the existing index until the new one is fully written.
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = INDEX_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(index, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_file.replace(INDEX_FILE)

    print(f"\nSaved {len(indexed_chunks)} vectors.")
    print(f"Numbers per vector: {dimensions}")
    print(f"Location: {INDEX_FILE}")


if __name__ == "__main__":
    main()