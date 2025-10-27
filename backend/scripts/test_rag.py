"""
Test script for the RAG pipeline.
Tests EDGAR scraping, Yahoo Finance, news aggregation, chunking, embeddings, and vector storage.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.database import MongoDB
from backend.services.chroma_client import chroma_db
from backend.rag.edgar_scraper import edgar_scraper
from backend.services.yahoo_finance import yahoo_finance
from backend.rag.news_aggregator import news_aggregator
from backend.rag.chunking import document_chunker
from backend.rag.embeddings import embedding_service
from backend.rag.vector_store import vector_store
from backend.rag.pipeline import rag_pipeline


async def test_database_connections():
    """Test database connections."""
    print("\n" + "="*60)
    print("TEST 1: Database Connections")
    print("="*60)

    try:
        # Connect to MongoDB
        await MongoDB.connect()
        print(f"✅ Connected to MongoDB: {MongoDB.db.name}")

        # Connect to ChromaDB
        chroma_db.connect()
        print(f"✅ Connected to ChromaDB: {chroma_db.collection.name}")
        print(f"   - Current document count: {chroma_db.count()}")

        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_yahoo_finance(ticker: str = "AAPL"):
    """Test Yahoo Finance integration."""
    print("\n" + "="*60)
    print(f"TEST 2: Yahoo Finance Integration ({ticker})")
    print("="*60)

    try:
        # Get stock info
        stock_info = yahoo_finance.get_stock_info(ticker)
        if stock_info:
            print(f"✅ Fetched stock info for {ticker}")
            print(f"   - Company: {stock_info.get('name')}")
            print(f"   - Price: ${stock_info.get('current_price')}")
            print(f"   - Market Cap: ${stock_info.get('market_cap'):,}" if stock_info.get('market_cap') else "   - Market Cap: N/A")
        else:
            print(f"❌ Failed to fetch stock info for {ticker}")
            return False

        # Get fundamentals
        fundamentals = yahoo_finance.get_fundamentals(ticker)
        if fundamentals:
            print(f"✅ Fetched fundamentals for {ticker}")
            pe = fundamentals.get('valuation', {}).get('pe_ratio')
            print(f"   - P/E Ratio: {pe}")
        else:
            print(f"⚠️  No fundamentals available for {ticker}")

        # Get news
        news = yahoo_finance.get_news(ticker, limit=5)
        print(f"✅ Fetched {len(news)} news items for {ticker}")
        if news:
            print(f"   - Latest: {news[0].get('title', 'N/A')[:60]}...")

        return True
    except Exception as e:
        print(f"❌ Yahoo Finance test failed: {e}")
        return False


async def test_news_aggregator(ticker: str = "AAPL"):
    """Test news aggregator."""
    print("\n" + "="*60)
    print(f"TEST 3: News Aggregator ({ticker})")
    print("="*60)

    try:
        # Get news summary
        summary = news_aggregator.get_news_summary(ticker, limit=10)
        print(f"✅ Aggregated {summary['count']} news items")

        if summary['news']:
            print(f"   - Latest: {summary['news'][0].get('title', 'N/A')[:60]}...")
            print(f"   - Latest date: {summary['latest_date']}")

            # Test keyword filtering
            filtered = news_aggregator.filter_by_keywords(
                summary['news'],
                keywords=["earnings", "revenue", "stock"]
            )
            print(f"✅ Filtered to {len(filtered)} items with keywords")

            # Test trending topics
            trending = news_aggregator.get_trending_topics(summary['news'], top_n=3)
            if trending:
                print(f"✅ Top trending topics:")
                for topic in trending:
                    print(f"   - {topic['topic']}: {topic['count']} mentions")

        return True
    except Exception as e:
        print(f"❌ News aggregator test failed: {e}")
        return False


async def test_document_chunking():
    """Test document chunking."""
    print("\n" + "="*60)
    print("TEST 4: Document Chunking")
    print("="*60)

    try:
        # Create sample document
        sample_text = """
        Apple Inc. reported strong quarterly earnings, beating analyst expectations.
        Revenue grew 15% year-over-year to $89.5 billion. iPhone sales remained robust
        despite supply chain challenges. The company announced a new $90 billion share
        buyback program and increased its dividend by 5%. Management expressed confidence
        in continued growth driven by services and wearables segments.
        """ * 10  # Repeat to create a longer document

        # Test basic chunking
        chunks = document_chunker.chunk_text(sample_text)
        print(f"✅ Chunked text into {len(chunks)} chunks")

        # Test token counting
        total_tokens = document_chunker.count_tokens(sample_text)
        print(f"   - Total tokens: {total_tokens}")
        print(f"   - First chunk tokens: {document_chunker.count_tokens(chunks[0])}")

        # Test document chunking with metadata
        chunk_docs = document_chunker.chunk_document(
            text=sample_text,
            source="test",
            ticker="AAPL",
            doc_type="earnings",
            date="2024-01-15"
        )
        print(f"✅ Created {len(chunk_docs)} chunk documents with metadata")
        print(f"   - First chunk metadata: {chunk_docs[0]['metadata']}")

        return True
    except Exception as e:
        print(f"❌ Document chunking test failed: {e}")
        return False


async def test_embeddings():
    """Test embedding generation."""
    print("\n" + "="*60)
    print("TEST 5: Embedding Generation")
    print("="*60)

    try:
        # Test single text embedding
        text = "Apple Inc. is a technology company that designs and sells consumer electronics."
        embedding = await embedding_service.embed_text(text)
        print(f"✅ Generated embedding for single text")
        print(f"   - Embedding dimension: {len(embedding)}")
        print(f"   - First 5 values: {embedding[:5]}")

        # Test batch embedding
        texts = [
            "Apple reported strong earnings.",
            "Microsoft cloud revenue grew 20%.",
            "Tesla announced new factory plans."
        ]
        embeddings = await embedding_service.embed_batch(texts, batch_size=3)
        print(f"✅ Generated {len(embeddings)} embeddings in batch")

        # Test document chunks embedding
        chunks = [
            {"text": texts[0], "metadata": {"ticker": "AAPL"}},
            {"text": texts[1], "metadata": {"ticker": "MSFT"}},
            {"text": texts[2], "metadata": {"ticker": "TSLA"}}
        ]
        embedded_chunks = await embedding_service.embed_document_chunks(chunks)
        print(f"✅ Embedded {len(embedded_chunks)} document chunks")
        print(f"   - Sample chunk has embedding: {'embedding' in embedded_chunks[0]}")

        return True
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_vector_storage():
    """Test vector storage operations."""
    print("\n" + "="*60)
    print("TEST 6: Vector Storage")
    print("="*60)

    try:
        # Create sample embedded chunks
        sample_texts = [
            "Apple Inc. reported record revenue in Q1 2024.",
            "Microsoft Azure cloud services continue to grow.",
            "Tesla's automotive segment showed strong performance."
        ]

        # Create chunks with metadata
        chunks = []
        for i, text in enumerate(sample_texts):
            ticker = ["AAPL", "MSFT", "TSLA"][i]
            embedding = await embedding_service.embed_text(text)
            chunks.append({
                "text": text,
                "metadata": {
                    "ticker": ticker,
                    "source": "test",
                    "doc_type": "earnings",
                    "date": "2024-01-15"
                },
                "embedding": embedding
            })

        # Store chunks
        count = await vector_store.store_document_chunks(chunks)
        print(f"✅ Stored {count} chunks in vector store")

        # Test search
        query = "What are Apple's recent earnings?"
        query_embedding = await embedding_service.embed_query(query)

        results = await vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=3
        )
        formatted_results = vector_store._format_results(results)
        print(f"✅ Retrieved {len(formatted_results)} similar documents")

        if formatted_results:
            print(f"   - Top result: {formatted_results[0]['text'][:60]}...")
            print(f"   - Similarity: {formatted_results[0]['similarity']:.4f}")

        # Test ticker filtering
        ticker_results = await vector_store.search_by_ticker(
            ticker="AAPL",
            query_embedding=query_embedding,
            top_k=2
        )
        print(f"✅ Retrieved {len(ticker_results)} documents for AAPL")

        # Test document count
        total_docs = await vector_store.get_document_count()
        aapl_docs = await vector_store.get_document_count(ticker="AAPL")
        print(f"✅ Document counts - Total: {total_docs}, AAPL: {aapl_docs}")

        return True
    except Exception as e:
        print(f"❌ Vector storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_pipeline(ticker: str = "AAPL"):
    """Test end-to-end RAG pipeline."""
    print("\n" + "="*60)
    print(f"TEST 7: End-to-End RAG Pipeline ({ticker})")
    print("="*60)

    try:
        # Test Yahoo Finance ingestion
        print(f"\n📥 Ingesting Yahoo Finance data for {ticker}...")
        yahoo_count = await rag_pipeline.ingest_yahoo_data(ticker)
        print(f"✅ Ingested {yahoo_count} chunks from Yahoo Finance")

        # Test news ingestion
        print(f"\n📥 Ingesting news for {ticker}...")
        news_count = await rag_pipeline.ingest_news(ticker, num_articles=5)
        print(f"✅ Ingested {news_count} chunks from news")

        # Test context retrieval
        print(f"\n🔍 Testing context retrieval...")
        query = f"What is {ticker}'s current financial situation?"
        context = await rag_pipeline.retrieve_context(
            query=query,
            ticker=ticker,
            top_k=3
        )
        print(f"✅ Retrieved {len(context)} relevant chunks")

        if context:
            print(f"\n📄 Top result:")
            print(f"   - Text: {context[0]['text'][:100]}...")
            print(f"   - Source: {context[0]['metadata'].get('source')}")
            print(f"   - Similarity: {context[0]['similarity']:.4f}")

        # Get ticker summary
        print(f"\n📊 Getting ticker summary...")
        summary = await rag_pipeline.get_ticker_summary(ticker)
        print(f"✅ Ticker summary for {ticker}:")
        print(f"   - Total docs: {summary['total_docs']}")
        print(f"   - Yahoo docs: {summary['yahoo_docs']}")
        print(f"   - News docs: {summary['news_docs']}")

        return True
    except Exception as e:
        print(f"❌ RAG pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all RAG pipeline tests."""
    print("\n" + "="*60)
    print("RAG PIPELINE TEST SUITE")
    print("="*60)

    results = {}

    # Test 1: Database connections
    results["database"] = await test_database_connections()

    # Test 2: Yahoo Finance
    results["yahoo_finance"] = await test_yahoo_finance()

    # Test 3: News aggregator
    results["news_aggregator"] = await test_news_aggregator()

    # Test 4: Document chunking
    results["chunking"] = await test_document_chunking()

    # Test 5: Embeddings
    results["embeddings"] = await test_embeddings()

    # Test 6: Vector storage
    results["vector_storage"] = await test_vector_storage()

    # Test 7: End-to-end RAG pipeline
    results["rag_pipeline"] = await test_rag_pipeline()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! RAG pipeline is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")

    # Close connections
    await MongoDB.close()

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
