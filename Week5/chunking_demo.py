"""Terminal demo for fixed, overlapping, document-aware, recursive, and semantic chunking."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from chunking_strategies import (
    Chunk,
    document_aware_chunks,
    fixed_size_chunks,
    overlapping_chunks,
    recursive_character_chunks,
    semantic_chunks,
)
from pretty_print import kv, preview, section, step


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def print_chunks(title: str, chunks: Iterable[Chunk], limit: int, max_chars: int) -> None:
    chunks = list(chunks)
    step(f"{title} ({len(chunks)} chunks)")
    for chunk in chunks[:limit]:
        heading = (chunk.metadata or {}).get("heading")
        parent = f" | parent={chunk.parent_id}" if chunk.parent_id else ""
        heading_text = f" | heading={heading}" if heading else ""
        print(f"\n[{chunk.chunk_id}] strategy={chunk.strategy}{parent}{heading_text}")
        preview(chunk.text[:max_chars] + ("..." if len(chunk.text) > max_chars else ""))


def run_demo(source: Path, limit: int) -> None:
    document = source.read_text(encoding="utf-8")

    section("Chunking Strategies Demo")
    kv("Source", source)
    kv("Characters", len(document))
    kv("Words", len(document.split()))
    preview(document[:420] + "...")

    print_chunks("1. Fixed-size chunking", fixed_size_chunks(document, chunk_size=55), limit, 320)
    print_chunks("2. Overlapping chunking", overlapping_chunks(document, chunk_size=55, overlap=15), limit, 320)
    print_chunks("3. Document-aware chunking", document_aware_chunks(document), limit, 420)
    print_chunks("4. Recursive chunking", recursive_character_chunks(document, chunk_size=650, overlap=80), limit, 420)
    print_chunks("5. Semantic chunking", semantic_chunks(document, similarity_threshold=0.18), limit, 320)

    section("Teaching Takeaway")
    preview(
        "Fixed-size chunks are simple but blind to meaning. Overlap protects boundary "
        "information. Document-aware and recursive chunking preserve structure. Semantic "
        "chunking follows topic shifts."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DATA_DIR / "company_ai_handbook.md")
    parser.add_argument("--limit", type=int, default=3, help="How many chunks to print per strategy.")
    args = parser.parse_args()
    run_demo(args.source, args.limit)


if __name__ == "__main__":
    main()
