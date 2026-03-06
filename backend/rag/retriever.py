"""
Hybrid retriever combining dense (vector) and sparse (BM25/TF-IDF) retrieval
with Reciprocal Rank Fusion (RRF).
"""
import logging
import math
from collections import Counter

logger = logging.getLogger(__name__)

_RRF_K = 60  # RRF smoothing constant


class HybridRetriever:
    """
    Combines dense vector search and a simple in-memory BM25 approximation
    via Reciprocal Rank Fusion (RRF).

    Args:
        vector_store: A QdrantVectorStore instance.
        embedder: An Embedder instance.
    """

    def __init__(self, vector_store, embedder) -> None:
        self._vector_store = vector_store
        self._embedder = embedder
        # Cache of indexed chunks for sparse retrieval
        self._chunks: list[dict] = []
        self._term_freqs: list[Counter] = []
        self._avg_doc_len: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_texts(self, chunks: list[dict]) -> None:
        """
        Index a list of chunk dicts.

        - Stores chunks for in-memory BM25.
        - Embeds texts and upserts into the vector store.

        Args:
            chunks: List of {"text": str, "metadata": dict}.
        """
        if not chunks:
            return

        texts = [c.get("text", "") for c in chunks]
        embeddings = self._embedder.embed(texts)
        self._vector_store.upsert(chunks, embeddings)

        # Update sparse index
        self._chunks.extend(chunks)
        new_tfs = [self._tokenize(t) for t in texts]
        self._term_freqs.extend(new_tfs)
        total_words = sum(sum(tf.values()) for tf in self._term_freqs)
        self._avg_doc_len = (
            total_words / len(self._term_freqs) if self._term_freqs else 0.0
        )

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve the top_k most relevant chunks using hybrid RRF fusion.

        Args:
            query: Natural language query string.
            top_k: Number of results to return.

        Returns:
            List of {"text": str, "metadata": dict, "score": float}
        """
        query_embedding = self._embedder.embed_query(query)

        # Dense retrieval: more candidates for RRF
        candidate_k = max(top_k * 3, 20)
        dense_results = self._vector_store.search(query_embedding, top_k=candidate_k)

        # Sparse retrieval
        sparse_results = self._sparse_search(query, top_k=candidate_k)

        # RRF fusion
        fused = self._rrf_fuse(dense_results, sparse_results)

        return fused[:top_k]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> Counter:
        """Simple whitespace + lower-case tokenizer."""
        words = text.lower().split()
        return Counter(words)

    def _sparse_search(self, query: str, top_k: int) -> list[dict]:
        """
        BM25-style keyword search over cached chunks.
        Uses simplified BM25 (k1=1.5, b=0.75).
        """
        if not self._chunks:
            return []

        query_terms = self._tokenize(query)
        k1, b = 1.5, 0.75
        n_docs = len(self._term_freqs)
        avg_dl = self._avg_doc_len or 1.0

        scores: list[tuple[float, int]] = []
        for idx, tf in enumerate(self._term_freqs):
            doc_len = sum(tf.values()) or 1
            score = 0.0
            for term, qf in query_terms.items():
                if term not in tf:
                    continue
                df = sum(1 for t in self._term_freqs if term in t)
                idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)
                tf_norm = (tf[term] * (k1 + 1)) / (
                    tf[term] + k1 * (1 - b + b * doc_len / avg_dl)
                )
                score += idf * tf_norm
            if score > 0:
                scores.append((score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "text": self._chunks[idx].get("text", ""),
                "metadata": self._chunks[idx].get("metadata", {}),
                "score": float(s),
            }
            for s, idx in scores[:top_k]
        ]

    @staticmethod
    def _rrf_fuse(
        dense: list[dict],
        sparse: list[dict],
    ) -> list[dict]:
        """
        Reciprocal Rank Fusion: score = Σ(1 / (rank + K)).

        Deduplicates by text content.
        """
        rrf_scores: dict[str, float] = {}
        text_to_result: dict[str, dict] = {}

        for rank, result in enumerate(dense):
            key = result["text"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (rank + _RRF_K)
            text_to_result[key] = result

        for rank, result in enumerate(sparse):
            key = result["text"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (rank + _RRF_K)
            if key not in text_to_result:
                text_to_result[key] = result

        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {**text_to_result[text], "score": score}
            for text, score in ranked
        ]
