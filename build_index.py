import argparse
import hashlib
import json
from getpass import getpass
from pathlib import Path

from openai import OpenAI


ROOT = Path(__file__).resolve().parent
CHUNKS_FILE = ROOT / "artifacts" / "chunks-700.jsonl"
INDEX_FILE = ROOT / "artifacts" / "vector-index.json"

ENDPOINT = (
    "https://yahya-onboarding-rag-resource"
    ".services.ai.azure.com/openai/v1/"
)
EMBEDDING_MODEL = "text-embedding-3-small"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=700)
    args = parser.parse_args()
    chunks_file = ROOT / "artifacts" / f"chunks-{args.size}.jsonl"
    if not chunks_file.exists():
        raise SystemExit(
            "Chunks file missing. Run: python -m onboarding prepare"
        )

    source_bytes = chunks_file.read_bytes()
    chunks = [
        json.loads(line)
        for line in source_bytes.decode("utf-8-sig").splitlines()
        if line.strip()
    ]

    if not chunks:
        raise SystemExit("The chunks file is empty.")

    for chunk in chunks:
        if not chunk.get("text", "").strip():
            raise SystemExit("Found an empty chunk. Prepare documents again.")

    print(f"Loaded {len(chunks)} document chunks.")

    api_key = getpass("Paste your Azure API key, then press Enter: ").strip()
    if not api_key:
        raise SystemExit("No API key entered.")

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
                f"Embedding chunks {start + 1}"
                f"–{start + len(batch)} of {len(chunks)}...",
                flush=True,
            )

            result = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=[chunk["text"] for chunk in batch],
                encoding_format="float",
            )

            # Match each returned vector to its original chunk.
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
        # Lets us detect if the source chunks change later.
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "chunks": indexed_chunks,
    }

    # Replace the index only after all embeddings finish successfully.
    temporary_file = INDEX_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(index, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_file.replace(INDEX_FILE)

    print(f"\nSaved {len(indexed_chunks)} vectors.")
    print(f"Numbers per vector: {dimensions}")
    print(f"Location: {INDEX_FILE}")
    print("Ready for semantic search.")


if __name__ == "__main__":
    main()