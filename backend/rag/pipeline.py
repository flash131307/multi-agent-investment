"""
End-to-end RAG pipeline for document ingestion and retrieval.
Integrates EDGAR scraper, Yahoo Finance, chunking, embeddings, and vector storage.
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from backend.rag.edgar_scraper import edgar_scraper
from backend.services.yahoo_finance import yahoo_finance
from backend.rag.chunking import document_chunker
from backend.rag.embeddings import embedding_service
from backend.rag.vector_store import vector_store

logger = logging.getLogger(__name__)


class RAGPipeline:
    """End-to-end RAG pipeline for financial documents."""

    def __init__(self):
        """Initialize pipeline components."""
        self.edgar = edgar_scraper
        self.yahoo = yahoo_finance
        self.chunker = document_chunker
        self.embedder = embedding_service
        self.vector_store = vector_store

    async def ingest_edgar_filing(
        self,
        ticker: str,
        filing_type: str = "10-K",
        num_filings: int = 1
    ) -> int:
        """
        Ingest SEC EDGAR filings for a ticker.

        Flow:
        1. Download filing from SEC EDGAR
        2. Parse and extract sections
        3. Chunk sections into optimal sizes
        4. Generate embeddings
        5. Store in vector database

        Args:
            ticker: Stock ticker
            filing_type: Type of filing ("10-K", "10-Q", etc.)
            num_filings: Number of filings to ingest

        Returns:
            Number of chunks ingested
        """
        logger.info(f"🚀 Starting EDGAR ingestion for {ticker} ({filing_type})")

        try:
            # 1. Download and parse filings
            filings = self.edgar.get_filing_summary(ticker, filing_type, num_filings)

            if not filings:
                logger.warning(f"No filings found for {ticker}")
                return 0

            total_chunks = 0

            for filing in filings:
                # 2. Chunk the filing
                chunks = self.chunker.chunk_edgar_filing(filing)

                if not chunks:
                    continue

                # 3. Generate embeddings
                embedded_chunks = await self.embedder.embed_document_chunks(chunks)

                # 4. Store in vector database
                count = await self.vector_store.store_document_chunks(embedded_chunks)
                total_chunks += count

            logger.info(f"✅ Ingested {total_chunks} chunks from {len(filings)} filing(s)")
            return total_chunks

        except Exception as e:
            logger.error(f"❌ EDGAR ingestion failed for {ticker}: {e}")
            raise

    async def ingest_yahoo_data(self, ticker: str) -> int:
        """
        Ingest Yahoo Finance data for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            Number of chunks ingested
        """
        logger.info(f"🚀 Starting Yahoo Finance ingestion for {ticker}")

        try:
            # Get complete analysis
            analysis = self.yahoo.get_complete_analysis(ticker)

            # Format for LLM
            formatted_text = self.yahoo.format_for_llm(analysis)

            # Create chunks
            chunks = self.chunker.chunk_document(
                text=formatted_text,
                source="yfinance",
                ticker=ticker,
                doc_type="market_data",
                date=datetime.utcnow().isoformat()
            )

            # Generate embeddings
            embedded_chunks = await self.embedder.embed_document_chunks(chunks)

            # Store
            count = await self.vector_store.store_document_chunks(embedded_chunks)

            logger.info(f"✅ Ingested {count} chunks from Yahoo Finance data")
            return count

        except Exception as e:
            logger.error(f"❌ Yahoo Finance ingestion failed for {ticker}: {e}")
            raise

    async def ingest_news(
        self,
        ticker: str,
        num_articles: int = 10
    ) -> int:
        """
        Ingest financial news for a ticker.

        Args:
            ticker: Stock ticker
            num_articles: Number of news articles to ingest

        Returns:
            Number of chunks ingested
        """
        logger.info(f"🚀 Starting news ingestion for {ticker}")

        try:
            # Get news from Yahoo Finance
            news_items = self.yahoo.get_news(ticker, limit=num_articles)

            if not news_items:
                logger.warning(f"No news found for {ticker}")
                return 0

            all_chunks = []

            for idx, news in enumerate(news_items):
                # Create text from news item
                text = f"Title: {news.get('title', 'No title')}\n"
                text += f"Publisher: {news.get('publisher', 'Unknown')}\n"
                text += f"Published: {news.get('publish_time', 'Unknown')}\n"
                if news.get('link'):
                    text += f"Link: {news['link']}\n"

                # Chunk news item with unique index
                chunks = self.chunker.chunk_document(
                    text=text,
                    source="news",
                    ticker=ticker,
                    doc_type="news_article",
                    date=news.get('publish_time', '')
                )

                # Add news index to make chunks unique
                for chunk in chunks:
                    chunk['metadata']['news_index'] = idx

                all_chunks.extend(chunks)

            # Generate embeddings for all chunks
            embedded_chunks = await self.embedder.embed_document_chunks(all_chunks)

            # Store
            count = await self.vector_store.store_document_chunks(embedded_chunks)

            logger.info(f"✅ Ingested {count} chunks from {len(news_items)} news articles")
            return count

        except Exception as e:
            logger.error(f"❌ News ingestion failed for {ticker}: {e}")
            raise

    async def ingest_all(
        self,
        ticker: str,
        include_edgar: bool = True,
        include_yahoo: bool = True,
        include_news: bool = True
    ) -> Dict[str, int]:
        """
        Ingest all data sources for a ticker.

        Args:
            ticker: Stock ticker
            include_edgar: Include EDGAR filings
            include_yahoo: Include Yahoo Finance data
            include_news: Include news articles

        Returns:
            Dict with counts for each source
        """
        logger.info(f"🚀 Starting full ingestion for {ticker}")

        counts = {
            "edgar": 0,
            "yahoo": 0,
            "news": 0,
            "total": 0
        }

        try:
            if include_edgar:
                counts["edgar"] = await self.ingest_edgar_filing(ticker, "10-K", num_filings=1)

            if include_yahoo:
                counts["yahoo"] = await self.ingest_yahoo_data(ticker)

            if include_news:
                counts["news"] = await self.ingest_news(ticker, num_articles=10)

            counts["total"] = sum([counts["edgar"], counts["yahoo"], counts["news"]])

            logger.info(f"✅ Full ingestion complete for {ticker}: {counts['total']} total chunks")
            return counts

        except Exception as e:
            logger.error(f"❌ Full ingestion failed for {ticker}: {e}")
            raise

    async def retrieve_context(
        self,
        query: str,
        ticker: Optional[str] = None,
        source: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query.

        Args:
            query: User query
            ticker: Filter by ticker (optional)
            source: Filter by source (optional)
            top_k: Number of results

        Returns:
            List of relevant document chunks
        """
        logger.info(f"🔍 Retrieving context for query: {query[:100]}...")

        try:
            # Generate query embedding
            query_embedding = await self.embedder.embed_query(query)

            # Search vector store
            results = await self.vector_store.hybrid_search(
                query_embedding=query_embedding,
                ticker=ticker,
                source=source,
                top_k=top_k
            )

            logger.info(f"✅ Retrieved {len(results)} relevant chunks")
            return results

        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {e}")
            raise

    async def has_deep_analysis_data(self, ticker: str) -> bool:
        """
        Check if deep analysis data (SEC 10-K) is available for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            True if EDGAR documents are available, False otherwise
        """
        try:
            edgar_count = await self.vector_store.get_document_count(ticker=ticker, source="edgar")
            return edgar_count > 0
        except Exception as e:
            logger.error(f"Failed to check deep analysis availability for {ticker}: {e}")
            return False

    async def get_ticker_summary(self, ticker: str) -> Dict[str, Any]:
        """
        Get summary of available data for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            Dict with data counts by source
        """
        return {
            "ticker": ticker.upper(),
            "edgar_docs": await self.vector_store.get_document_count(ticker=ticker, source="edgar"),
            "yahoo_docs": await self.vector_store.get_document_count(ticker=ticker, source="yfinance"),
            "news_docs": await self.vector_store.get_document_count(ticker=ticker, source="news"),
            "total_docs": await self.vector_store.get_document_count(ticker=ticker)
        }


# Singleton instance
rag_pipeline = RAGPipeline()
