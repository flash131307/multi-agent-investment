"""Qdrant-based vector store for the fundamental RAG pipeline."""

import logging
import uuid as _uuid

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """
    Thin wrapper around qdrant_client for storing and searching document embeddings.
    Supports in-memory mode (url=":memory:") and remote Qdrant instances.

    Raises:
        ImportError: If qdrant_client is not installed.
    """

    def __init__(
        self,
        url: str = ":memory:",
        collection_name: str = "investment_docs",
        api_key: str | None = None,
    ) -> None:
        try:
            from qdrant_client import QdrantClient  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "qdrant_client is required for QdrantVectorStore. "
                "Install it with: pip install qdrant-client"
            ) from exc

        self.collection_name = collection_name
        self._collection_created = False

        if url == ":memory:":
            self._client = QdrantClient(location=":memory:")
        else:
            init_kwargs: dict = {"url": url}
            if api_key:
                init_kwargs["api_key"] = api_key
            self._client = QdrantClient(**init_kwargs)

    def _ensure_collection(self, dim: int) -> None:
        """Create the collection if it does not yet exist."""
        if self._collection_created:
            return

        from qdrant_client.models import Distance, VectorParams  # type: ignore

        existing = {c.name for c in self._client.get_collections().collections}
        if self.collection_name not in existing:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            logger.info(
                "Created Qdrant collection '%s' (dim=%d)", self.collection_name, dim
            )
        self._collection_created = True

    def upsert(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        """
        Upsert document chunks with their embeddings.

        Args:
            chunks: List of dicts with "text" and "metadata" keys.
            embeddings: Parallel list of float vectors.

        Returns:
            Number of points upserted.
        """
        if not chunks or not embeddings:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) "
                "must be the same length"
            )

        dim = len(embeddings[0])
        self._ensure_collection(dim)

        from qdrant_client.models import PointStruct  # type: ignore

        points = [
            PointStruct(
                id=str(_uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": chunk.get("text", ""),
                    "metadata": chunk.get("metadata", {}),
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self._client.upsert(collection_name=self.collection_name, points=points)
        logger.debug("Upserted %d points into '%s'", len(points), self.collection_name)
        return len(points)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        """
        Nearest-neighbour search.

        Returns:
            List of dicts: {"text": str, "metadata": dict, "score": float}
        """
        if not self._collection_created:
            return []

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore

            query_filter = None
            if metadata_filter:
                conditions = [
                    FieldCondition(key=f"metadata.{k}", match=MatchValue(value=v))
                    for k, v in metadata_filter.items()
                ]
                query_filter = Filter(must=conditions)

            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
            )
        except Exception as exc:
            logger.error("Qdrant search failed: %s", exc)
            return []

        return [
            {
                "text": hit.payload.get("text", ""),
                "metadata": hit.payload.get("metadata", {}),
                "score": float(hit.score),
            }
            for hit in results
        ]

    def count(self) -> int:
        """Return number of points in the collection."""
        if not self._collection_created:
            return 0
        try:
            return self._client.count(collection_name=self.collection_name).count
        except Exception as exc:
            logger.error("Qdrant count failed: %s", exc)
            return 0

    def delete_collection(self) -> None:
        """Drop the collection (useful for test cleanup)."""
        try:
            self._client.delete_collection(collection_name=self.collection_name)
            self._collection_created = False
            logger.info("Deleted Qdrant collection '%s'", self.collection_name)
        except Exception as exc:
            logger.warning(
                "Could not delete collection '%s': %s", self.collection_name, exc
            )
