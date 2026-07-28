"""Embedding helpers for the RAG demos.

The LanceDB demos use a Hugging Face sentence-transformers model by default.
`HashingEmbedder` remains available as a tiny deterministic fallback for moments
when you want to teach the retrieval pipeline without model downloads.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Iterable, List, Protocol


DEFAULT_HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_'-]*")


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class Embedder(Protocol):
    dimensions: int

    def encode_one(self, text: str) -> List[float]:
        ...

    def encode(self, texts: Iterable[str]) -> List[List[float]]:
        ...


class SentenceTransformerEmbedder:
    """Hugging Face sentence-transformers embedder."""

    def __init__(self, model_name: str = DEFAULT_HF_EMBEDDING_MODEL):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for Hugging Face embeddings. "
                "Install dependencies with: python3 -m pip install -r requirements.txt"
            ) from exc

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimensions = int(self.model.get_sentence_embedding_dimension())

    def encode_one(self, text: str) -> List[float]:
        return self.encode([text])[0]

    def encode(self, texts: Iterable[str]) -> List[List[float]]:
        vectors = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


class HashingEmbedder:
    """A small hashing-vectorizer style embedder with L2 normalization."""

    def __init__(self, dimensions: int = 128):
        self.dimensions = dimensions

    def encode_one(self, text: str) -> List[float]:
        vector = [0.0] * self.dimensions
        counts = Counter(tokenize(text))
        for token, count in counts.items():
            digest = hashlib.md5(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign * (1.0 + math.log(count))

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def encode(self, texts: Iterable[str]) -> List[List[float]]:
        return [self.encode_one(text) for text in texts]


def make_embedder(
    backend: str = "hf",
    model_name: str = DEFAULT_HF_EMBEDDING_MODEL,
    hash_dimensions: int = 128,
) -> Embedder:
    if backend == "hf":
        return SentenceTransformerEmbedder(model_name)
    if backend == "hash":
        return HashingEmbedder(dimensions=hash_dimensions)
    raise ValueError(f"Unknown embedding backend: {backend}")


def cosine_similarity(left: List[float], right: List[float]) -> float:
    return sum(a * b for a, b in zip(left, right))
