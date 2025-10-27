"""
OpenAI embedding service for generating vector embeddings.
Uses text-embedding-3-small for cost-effective embeddings.
"""
from openai import AsyncOpenAI
from typing import List, Dict, Any
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
        self.embedding_dim = 1536  # text-embedding-3-small dimension

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats (embedding vector)
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )

            embedding = response.data[0].embedding
            return embedding

        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call (max 100 for OpenAI)

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.info(f"✅ Generated embeddings for batch {i//batch_size + 1} ({len(batch)} texts)")

                # Small delay to avoid rate limits
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"❌ Failed to generate batch embeddings: {e}")
                raise

        logger.info(f"✅ Generated {len(all_embeddings)} total embeddings")
        return all_embeddings

    async def embed_document_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for document chunks.

        Args:
            chunks: List of dicts with 'text' and 'metadata' keys

        Returns:
            List of dicts with 'text', 'metadata', and 'embedding' keys
        """
        # Extract texts
        texts = [chunk["text"] for chunk in chunks]

        # Generate embeddings
        embeddings = await self.embed_batch(texts)

        # Add embeddings to chunks
        embedded_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            embedded_chunks.append({
                **chunk,
                "embedding": embedding
            })

        logger.info(f"✅ Embedded {len(embedded_chunks)} document chunks")
        return embedded_chunks

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        return await self.embed_text(query)

    def get_embedding_cost(self, num_tokens: int) -> float:
        """
        Calculate cost for embeddings.

        text-embedding-3-small: $0.02 per 1M tokens

        Args:
            num_tokens: Number of tokens to embed

        Returns:
            Cost in USD
        """
        cost_per_million = 0.02
        cost = (num_tokens / 1_000_000) * cost_per_million
        return cost


# Singleton instance
embedding_service = EmbeddingService()
