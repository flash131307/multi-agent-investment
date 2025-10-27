"""
ChromaDB client for local vector storage.
Handles document embeddings and similarity search.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional, Any
import logging
import os

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class ChromaDB:
    """ChromaDB client manager."""

    def __init__(self):
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None

    def connect(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Ensure persist directory exists
            os.makedirs(settings.chroma_persist_dir, exist_ok=True)

            # Initialize client with persistence
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )

            logger.info(f"✅ Connected to ChromaDB: {settings.chroma_collection_name}")
            logger.info(f"📊 Collection count: {self.collection.count()}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            raise

    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Add documents to ChromaDB collection.

        Args:
            ids: Unique IDs for each document
            documents: Text content of documents
            embeddings: Vector embeddings (1536 dims for OpenAI)
            metadatas: Optional metadata dicts (ticker, date, source, etc.)
        """
        if self.collection is None:
            self.connect()

        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"✅ Added {len(ids)} documents to ChromaDB")

        except Exception as e:
            logger.error(f"❌ Failed to add documents to ChromaDB: {e}")
            raise

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query ChromaDB for similar documents.

        Args:
            query_embeddings: Query vector(s)
            n_results: Number of results to return
            where: Metadata filter (e.g., {"ticker": "AAPL"})
            where_document: Document content filter

        Returns:
            Dict with ids, documents, metadatas, distances
        """
        if self.collection is None:
            self.connect()

        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results

        except Exception as e:
            logger.error(f"❌ ChromaDB query failed: {e}")
            raise

    def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get documents by ID or metadata filter.

        Args:
            ids: Document IDs to retrieve
            where: Metadata filter
            limit: Max number of results

        Returns:
            Dict with ids, documents, metadatas, embeddings
        """
        if self.collection is None:
            self.connect()

        try:
            return self.collection.get(
                ids=ids,
                where=where,
                limit=limit
            )
        except Exception as e:
            logger.error(f"❌ ChromaDB get failed: {e}")
            raise

    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ):
        """
        Delete documents by ID or metadata filter.

        Args:
            ids: Document IDs to delete
            where: Metadata filter for deletion
        """
        if self.collection is None:
            self.connect()

        try:
            self.collection.delete(ids=ids, where=where)
            logger.info(f"✅ Deleted documents from ChromaDB")

        except Exception as e:
            logger.error(f"❌ ChromaDB delete failed: {e}")
            raise

    def count(self) -> int:
        """Get total number of documents in collection."""
        if self.collection is None:
            self.connect()
        return self.collection.count()

    def reset(self):
        """Reset the collection (delete all documents)."""
        if self.client is None:
            self.connect()

        try:
            self.client.delete_collection(settings.chroma_collection_name)
            self.collection = self.client.create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("✅ ChromaDB collection reset")

        except Exception as e:
            logger.error(f"❌ Failed to reset ChromaDB: {e}")
            raise


# Singleton instance
chroma_db = ChromaDB()
