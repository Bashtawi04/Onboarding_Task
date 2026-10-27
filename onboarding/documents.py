"""Read approved documents and split them into searchable chunks."""

import re
import unicodedata
from pathlib import Path

import pymupdf

from .records import read_csv


def manifest(data: Path) -> list[dict]:
    # Only current registered policies enter the search collection.
    rows = [
        row
        for row in read_csv(data / "policy_register.csv")
        if row["status"] == "Current"
    ]

    # These supplied documents have no entry in the policy register.
    for path in [
        "arabic/Welcome_Letter_AR_EN.pdf",
        "mol_guidance/mol_digest_onboarding.md",
    ]:
        rows.append({
            "file_path": path,
            "doc_id": None,
            "version": None,
            "status": "UnregisteredSupplement",
            "authority_rank": None,
        })

    return rows


def clean_text(text: str) -> str:
    # Normalize characters, including Arabic presentation forms.
    text = unicodedata.normalize("NFKC", text)

    lines = []
    for line in text.splitlines():
        if re.search(
            r"fictional training data|Page\s+\d+\s+of\s+\d+",
            line,
            re.IGNORECASE,
        ):
            continue

        line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(line)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def read_pages(path: Path):
    if path.suffix.lower() == ".pdf":
        with pymupdf.open(path) as document:
            for number, page in enumerate(document, start=1):
                yield number, page.get_text("text", sort=False)
    else:
        yield None, path.read_text(encoding="utf-8-sig")


def split_text(text: str, size: int, overlap: int):
    start = 0

    while start < len(text):
        end = min(start + size, len(text))

        # Prefer ending at a word boundary.
        if end < len(text):
            boundaries = list(
                re.finditer(r"\s+", text[start:end])
            )
            if boundaries:
                boundary = start + boundaries[-1].start()
                if boundary > start + size // 2:
                    end = boundary

        fragment = text[start:end].strip()
        if fragment:
            yield start, fragment

        if end >= len(text):
            break

        next_start = max(start + 1, end - overlap)

        # Avoid beginning halfway through a word.
        while (
            next_start < end
            and next_start > 0
            and not text[next_start - 1].isspace()
        ):
            next_start += 1

        start = next_start


def chunks(data: Path, size: int = 700, overlap: int = 100):
    if not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < size")

    for metadata in manifest(data):
        path = data / metadata["file_path"]

        for page, raw in read_pages(path):
            text = clean_text(raw)

            if not text:
                raise ValueError(
                    f"No readable text: {path.name}, page {page}. "
                    "This page may need OCR."
                )

            for offset, fragment in split_text(text, size, overlap):
                yield {
                    **metadata,
                    "page": page,
                    "offset": offset,
                    "chunk_id": (
                        f"{metadata['file_path']}:"
                        f"{page or 'md'}:{offset}"
                    ),
                    "text": fragment,
                    # Preserve context for tables and nearby rules.
                    "page_text": text,
                }