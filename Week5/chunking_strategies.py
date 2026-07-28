"""Chunking strategies for RAG teaching demos."""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List

from simple_embeddings import HashingEmbedder, cosine_similarity


SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    strategy: str
    parent_id: str | None = None
    metadata: Dict[str, object] | None = None

    def as_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["metadata"] = payload["metadata"] or {}
        return payload


def words(text: str) -> List[str]:
    return re.findall(r"\S+", text)


def fixed_size_chunks(text: str, chunk_size: int = 80) -> List[Chunk]:
    tokens = words(text)
    chunks = []
    for start in range(0, len(tokens), chunk_size):
        chunk_words = tokens[start : start + chunk_size] # list of words in a particular chunk
        chunks.append(
            Chunk(
                chunk_id=f"fixed-{len(chunks):03d}",
                text=" ".join(chunk_words),
                strategy="fixed_size",
                metadata={"start_word": start, "end_word": start + len(chunk_words)},
            )
        )
    return chunks


def overlapping_chunks(text: str, chunk_size: int = 80, overlap: int = 20) -> List[Chunk]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    tokens = words(text)
    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(tokens), step):
        chunk_words = tokens[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(
            Chunk(
                chunk_id=f"overlap-{len(chunks):03d}",
                text=" ".join(chunk_words),
                strategy="overlapping",
                metadata={
                    "start_word": start,
                    "end_word": start + len(chunk_words),
                    "overlap_words": overlap,
                },
            )
        )
        if start + chunk_size >= len(tokens):
            break
    return chunks


# this func does the axctual splitting
def split_markdown_sections(markdown: str) -> List[tuple[str, str]]:
    matches = list(re.finditer(r"^##\s+(.+)$", markdown, flags=re.MULTILINE))
    sections = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        title = match.group(1).strip()
        sections.append((title, markdown[start:end].strip()))
    return sections or [("Document", markdown.strip())]


# goes over each spilt and forms chunk objects
def document_aware_chunks(markdown: str) -> List[Chunk]:
    chunks = []
    for section_index, (title, body) in enumerate(split_markdown_sections(markdown), start=1):
        chunks.append(
            Chunk(
                chunk_id=f"section-{section_index:03d}",
                text=body,
                strategy="document_aware",
                metadata={"heading": title, "section_number": section_index},
            )
        )
    return chunks


def recursive_character_chunks(
    text: str,
    chunk_size: int = 700,
    overlap: int = 80,
    separators: Iterable[str] = ("\n## ", "\n\n", ". ", " "),
) -> List[Chunk]:
    pieces = _recursive_split(text, chunk_size, list(separators))
    chunks = []
    carry = "" 
    for piece in pieces:
        merged = (carry + " " + piece).strip() if carry else piece.strip()
        if merged:
            chunks.append(
                Chunk(
                    chunk_id=f"recursive-{len(chunks):03d}",
                    text=merged,
                    strategy="recursive",
                    metadata={"max_chars": chunk_size, "overlap_chars": overlap},
                )
            )
        carry = merged[-overlap:] if overlap else "" # store the overlapping part from the last chunk
    return chunks


def _recursive_split(text: str, chunk_size: int, separators: List[str]) -> List[str]:
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator = separators[0]
    # splitting our whole content using the separators
    raw_parts = text.split(separator)
    if len(raw_parts) == 1:
        return _recursive_split(text, chunk_size, separators[1:])

    parts = []
    for index, part in enumerate(raw_parts):
        if not part.strip():
            continue
        prefix = separator if index > 0 and separator.startswith("\n") else ""
        candidate = (prefix + part).strip()
        if len(candidate) <= chunk_size:
            parts.append(candidate)
        else:
            parts.extend(_recursive_split(candidate, chunk_size, separators[1:]))
    return _pack_parts(parts, chunk_size)


def _pack_parts(parts: List[str], chunk_size: int) -> List[str]:
    packed = []
    current = ""
    for part in parts:
        candidate = (current + "\n\n" + part).strip() if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                packed.append(current)
            current = part
    if current:
        packed.append(current)
    return packed


def semantic_chunks(text: str, similarity_threshold: float = 0.22) -> List[Chunk]:
    sentences = [sentence.strip() for sentence in SENTENCE_RE.split(text) if sentence.strip()]
    if not sentences:
        return []

    embedder = HashingEmbedder() # dummy embedder not something you need to understand; instead use a sent embedding model from hf
    vectors = embedder.encode(sentences)
    groups: List[List[str]] = [[sentences[0]]]
    break_scores = []

    for index in range(1, len(sentences)):
        similarity = cosine_similarity(vectors[index - 1], vectors[index])
        break_scores.append(round(similarity, 3))
        if similarity < similarity_threshold: # we have a chunk boundary
            groups.append([sentences[index]])
        else:
            groups[-1].append(sentences[index])

    return [
        Chunk(
            chunk_id=f"semantic-{index:03d}",
            text=" ".join(group),
            strategy="semantic",
            metadata={"similarity_threshold": similarity_threshold, "sentence_count": len(group)},
        )
        for index, group in enumerate(groups)
    ]
