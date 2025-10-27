"""
Vector store integration with ChromaDB for RAG pipeline.
Handles storage and retrieval of embedded documents.
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import hashlib

from backend.services.chroma_client import chroma_db

logger = logging.getLogger(__name__)


class DocumentVectorStore:
    """Manages document storage and retrieval in ChromaDB."""

    def __init__(self):
        """Initialize vector store."""
        self.chroma = chroma_db

    def _generate_id(self, text: str, metadata: Dict) -> str:
        """
        Generate unique ID for a document chunk.

        Args:
            text: Chunk text
            metadata: Chunk metadata

        Returns:
            Unique ID string
        """
        # Create ID from ticker, source, and text hash
        ticker = metadata.get("ticker", "UNKNOWN")
        source = metadata.get("source", "unknown")
        doc_type = metadata.get("doc_type", "")

        # Use full text + metadata for hash to ensure uniqueness
        # Include chunk_index and news_index if available to differentiate chunks
        chunk_index = metadata.get("chunk_index", "")
        news_index = metadata.get("news_index", "")

        # Create unique string from text and all metadata
        unique_string = f"{ticker}_{source}_{doc_type}_{chunk_index}_{news_index}_{text}"
        text_hash = hashlib.md5(unique_string.encode()).hexdigest()[:16]

        # Format: TICKER_SOURCE_DOCTYPE_HASH
        id_parts = [ticker, source, doc_type, text_hash]
        doc_id = "_".join(p for p in id_parts if p)

        return doc_id

    async def store_document_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Store document chunks with embeddings in ChromaDB.

        Args:
            chunks: List of dicts with 'text', 'metadata', and 'embedding' keys

        Returns:
            Number of chunks stored
        """
        if not chunks:
            logger.warning("No chunks to store")
            return 0

        try:
            # Generate IDs
            ids = [self._generate_id(chunk["text"], chunk["metadata"]) for chunk in chunks]

            # Extract components
            documents = [chunk["text"] for chunk in chunks]
            embeddings = [chunk["embedding"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]

            # Store in ChromaDB
            self.chroma.add_documents(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            logger.info(f"✅ Stored {len(chunks)} chunks in vector store")
            return len(chunks)

        except Exception as e:
            logger.error(f"❌ Failed to store chunks: {e}")
            raise

    async def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents using vector similarity.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"ticker": "AAPL"})

        Returns:
            ChromaDB query results
        """
        try:
            results = self.chroma.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )

            logger.info(f"✅ Found {len(results['documents'][0]) if results['documents'] else 0} similar documents")
            return results

        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            raise

    async def search_by_ticker(
        self,
        ticker: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search documents for a specific ticker.

        Args:
            ticker: Stock ticker
            query_embedding: Query vector
            top_k: Number of results

        Returns:
            List of matching documents with metadata
        """
        results = await self.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            filters={"ticker": ticker.upper()}
        )

        return self._format_results(results)

    async def search_by_date_range(
        self,
        start_date: str,
        end_date: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search documents within a date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            query_embedding: Query vector
            top_k: Number of results

        Returns:
            List of matching documents
        """
        # Note: ChromaDB metadata filters are exact match, not range
        # For date ranges, we'll fetch more results and filter in Python
        results = await self.search_similar(
            query_embedding=query_embedding,
            top_k=top_k * 3  # Fetch more to filter
        )

        # Filter by date range
        filtered = self._filter_by_date_range(results, start_date, end_date)
        return filtered[:top_k]

    async def search_by_source(
        self,
        source: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search documents from a specific source.

        Args:
            source: Source type ("edgar", "news", "yfinance")
            query_embedding: Query vector
            top_k: Number of results

        Returns:
            List of matching documents
        """
        results = await self.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            filters={"source": source}
        )

        return self._format_results(results)

    async def hybrid_search(
        self,
        query_embedding: List[float],
        ticker: Optional[str] = None,
        source: Optional[str] = None,
        doc_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity and metadata filters.

        Args:
            query_embedding: Query vector
            ticker: Filter by ticker (optional)
            source: Filter by source (optional)
            doc_type: Filter by document type (optional)
            top_k: Number of results

        Returns:
            List of matching documents
        """
        # Build metadata filter with proper ChromaDB syntax
        filter_conditions = []
        if ticker:
            filter_conditions.append({"ticker": ticker.upper()})
        if source:
            filter_conditions.append({"source": source})
        if doc_type:
            filter_conditions.append({"doc_type": doc_type})

        # ChromaDB requires $and for multiple conditions
        if len(filter_conditions) > 1:
            filters = {"$and": filter_conditions}
        elif len(filter_conditions) == 1:
            filters = filter_conditions[0]
        else:
            filters = None

        results = await self.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )

        return self._format_results(results)

    def _format_results(self, chroma_results: Dict) -> List[Dict[str, Any]]:
        """
        Format ChromaDB results into a cleaner structure.

        Args:
            chroma_results: Raw ChromaDB query results

        Returns:
            List of formatted result dicts
        """
        formatted = []

        if not chroma_results.get("documents") or not chroma_results["documents"][0]:
            return formatted

        # ChromaDB returns results nested in arrays
        documents = chroma_results["documents"][0]
        metadatas = chroma_results.get("metadatas", [[]])[0]
        distances = chroma_results.get("distances", [[]])[0]
        ids = chroma_results.get("ids", [[]])[0]

        for i in range(len(documents)):
            formatted.append({
                "id": ids[i] if i < len(ids) else None,
                "text": documents[i],
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
                "similarity": 1 - distances[i] if i < len(distances) else None  # Convert distance to similarity
            })

        return formatted

    def _filter_by_date_range(
        self,
        results: Dict,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Filter results by date range."""
        formatted = self._format_results(results)

        filtered = []
        for doc in formatted:
            doc_date = doc["metadata"].get("date", "")
            if start_date <= doc_date <= end_date:
                filtered.append(doc)

        return filtered

    async def get_document_count(
        self,
        ticker: Optional[str] = None,
        source: Optional[str] = None
    ) -> int:
        """
        Get count of documents in the store.

        Args:
            ticker: Filter by ticker (optional)
            source: Filter by source (optional)

        Returns:
            Document count
        """
        if not ticker and not source:
            return self.chroma.count()

        # For filtered counts, we need to query and count
        # ChromaDB requires $and operator for multiple filters
        if ticker and source:
            filters = {
                "$and": [
                    {"ticker": ticker.upper()},
                    {"source": source}
                ]
            }
        elif ticker:
            filters = {"ticker": ticker.upper()}
        else:
            filters = {"source": source}

        try:
            results = self.chroma.get(where=filters, limit=10000)
            return len(results.get("ids", []))
        except Exception as e:
            logger.error(f"❌ Failed to get document count: {e}")
            return 0

    async def delete_by_ticker(self, ticker: str):
        """Delete all documents for a ticker."""
        try:
            self.chroma.delete(where={"ticker": ticker.upper()})
            logger.info(f"✅ Deleted documents for {ticker}")
        except Exception as e:
            logger.error(f"❌ Failed to delete documents for {ticker}: {e}")
            raise


# Singleton instance
vector_store = DocumentVectorStore()
