"""Small BM25 fallback used when rank_bm25 is not installed."""

from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, List

from simple_embeddings import tokenize


class SimpleBM25:
    def __init__(self, documents: Iterable[str], k1: float = 1.5, b: float = 0.75):
        self.docs = [tokenize(doc) for doc in documents]
        # params of the bm25 algo that we can tune
        self.k1 = k1
        self.b = b
        self.avgdl = sum(len(doc) for doc in self.docs) / max(len(self.docs), 1)
        self.doc_freq = Counter()
        for doc in self.docs:
            self.doc_freq.update(set(doc))
        self.n_docs = len(self.docs)

    def get_scores(self, query: str) -> List[float]:
        query_terms = tokenize(query)
        scores = [] # score for all docs/chunks corresp to the query
        for doc in self.docs:
            frequencies = Counter(doc)
            doc_len = len(doc) or 1
            score = 0.0
            for term in query_terms:
                if term not in frequencies:
                    continue
                df = self.doc_freq.get(term, 0)
                idf = math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))
                tf = frequencies[term]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score += idf * numerator / denominator
            scores.append(score)
        return scores
