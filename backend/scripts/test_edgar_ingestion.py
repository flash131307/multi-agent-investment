"""
Test script for EDGAR filing ingestion.
Tests downloading and ingesting real SEC 10-K filings.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.database import MongoDB
from backend.services.chroma_client import chroma_db
from backend.rag.edgar_scraper import edgar_scraper
from backend.rag.pipeline import rag_pipeline


async def test_edgar_download(ticker: str = "AAPL"):
    """Test downloading EDGAR filing."""
    print("\n" + "="*60)
    print(f"TEST 1: Download EDGAR 10-K for {ticker}")
    print("="*60)

    try:
        # Download 10-K filing
        print(f"📥 Downloading 10-K filing for {ticker}...")
        edgar_scraper.download_filing(ticker, filing_type="10-K", num_filings=1)
        print(f"✅ Successfully downloaded 10-K for {ticker}")

        # Get filing summary
        print(f"\n📄 Parsing filing...")
        filings = edgar_scraper.get_filing_summary(ticker, filing_type="10-K", num_filings=1)

        if not filings:
            print(f"❌ No filings found for {ticker}")
            return False

        filing = filings[0]
        print(f"✅ Parsed filing:")
        print(f"   - Ticker: {filing['ticker']}")
        print(f"   - Filing Type: {filing['filing_type']}")
        print(f"   - Filing Date: {filing['filing_date']}")
        print(f"   - Sections found: {len(filing['sections'])}")

        # Show sections
        for section_name, content in filing['sections'].items():
            word_count = len(content.split())
            print(f"   - {section_name}: {word_count} words")

        return True

    except Exception as e:
        print(f"❌ EDGAR download failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_edgar_ingestion(ticker: str = "AAPL"):
    """Test full EDGAR ingestion pipeline."""
    print("\n" + "="*60)
    print(f"TEST 2: Ingest EDGAR 10-K into RAG Pipeline")
    print("="*60)

    try:
        # Connect to databases
        await MongoDB.connect()
        chroma_db.connect()
        print(f"✅ Connected to databases")

        # Get initial document count
        initial_count = await rag_pipeline.vector_store.get_document_count(ticker=ticker, source="edgar")
        print(f"📊 Initial EDGAR document count for {ticker}: {initial_count}")

        # Ingest EDGAR filing
        print(f"\n📥 Starting EDGAR ingestion for {ticker}...")
        print(f"   This may take a few minutes...")

        chunk_count = await rag_pipeline.ingest_edgar_filing(
            ticker=ticker,
            filing_type="10-K",
            num_filings=1
        )

        print(f"\n✅ Successfully ingested {chunk_count} chunks from 10-K")

        # Verify storage
        final_count = await rag_pipeline.vector_store.get_document_count(ticker=ticker, source="edgar")
        print(f"📊 Final EDGAR document count for {ticker}: {final_count}")
        print(f"📈 New chunks added: {final_count - initial_count}")

        # Test retrieval
        print(f"\n🔍 Testing retrieval with EDGAR data...")
        query = f"What are the main risk factors for {ticker}?"
        results = await rag_pipeline.retrieve_context(
            query=query,
            ticker=ticker,
            source="edgar",
            top_k=3
        )

        print(f"✅ Retrieved {len(results)} relevant chunks")
        if results:
            print(f"\n📄 Top result:")
            print(f"   - Section: {results[0]['metadata'].get('section', 'Unknown')}")
            print(f"   - Similarity: {results[0]['similarity']:.4f}")
            print(f"   - Text preview: {results[0]['text'][:200]}...")

        return True

    except Exception as e:
        print(f"❌ EDGAR ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await MongoDB.close()


async def test_multiple_tickers():
    """Test ingesting EDGAR filings for multiple tickers."""
    print("\n" + "="*60)
    print("TEST 3: Multi-Ticker EDGAR Ingestion")
    print("="*60)

    tickers = ["AAPL", "MSFT", "TSLA"]

    try:
        # Connect to databases
        await MongoDB.connect()
        chroma_db.connect()

        results = {}

        for ticker in tickers:
            print(f"\n📥 Ingesting {ticker}...")
            try:
                count = await rag_pipeline.ingest_edgar_filing(
                    ticker=ticker,
                    filing_type="10-K",
                    num_filings=1
                )
                results[ticker] = count
                print(f"✅ {ticker}: {count} chunks")
            except Exception as e:
                print(f"❌ {ticker} failed: {e}")
                results[ticker] = 0

        # Summary
        print(f"\n" + "="*60)
        print("INGESTION SUMMARY")
        print("="*60)

        total_chunks = 0
        for ticker, count in results.items():
            print(f"{ticker}: {count} chunks")
            total_chunks += count

        print(f"\nTotal chunks ingested: {total_chunks}")

        # Get total document count
        total_docs = await rag_pipeline.vector_store.get_document_count()
        print(f"Total documents in vector store: {total_docs}")

        return True

    except Exception as e:
        print(f"❌ Multi-ticker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await MongoDB.close()


async def test_cross_document_search():
    """Test searching across multiple documents."""
    print("\n" + "="*60)
    print("TEST 4: Cross-Document Search")
    print("="*60)

    try:
        # Connect to databases
        await MongoDB.connect()
        chroma_db.connect()

        # Test queries
        queries = [
            "What are the main business segments?",
            "What are the key risk factors?",
            "What is the revenue growth strategy?"
        ]

        for query in queries:
            print(f"\n🔍 Query: {query}")

            results = await rag_pipeline.retrieve_context(
                query=query,
                source="edgar",
                top_k=5
            )

            print(f"✅ Found {len(results)} results across all documents")

            # Group by ticker
            ticker_counts = {}
            for result in results:
                ticker = result['metadata'].get('ticker', 'Unknown')
                ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

            print(f"   Results by ticker:")
            for ticker, count in ticker_counts.items():
                print(f"   - {ticker}: {count} chunks")

            if results:
                print(f"   Top result: {results[0]['metadata'].get('ticker')} - "
                      f"{results[0]['metadata'].get('section')} "
                      f"(similarity: {results[0]['similarity']:.4f})")

        return True

    except Exception as e:
        print(f"❌ Cross-document search failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await MongoDB.close()


async def run_all_tests():
    """Run all EDGAR ingestion tests."""
    print("\n" + "="*60)
    print("EDGAR INGESTION TEST SUITE")
    print("="*60)

    results = {}

    # Test 1: Download EDGAR filing
    results["download"] = await test_edgar_download("AAPL")

    # Test 2: Full ingestion pipeline
    results["ingestion"] = await test_edgar_ingestion("AAPL")

    # Test 3: Multiple tickers (optional - takes longer)
    # Uncomment to test multiple tickers
    # results["multi_ticker"] = await test_multiple_tickers()

    # Test 4: Cross-document search (requires multiple documents)
    # Uncomment if you ran multi-ticker test
    # results["cross_search"] = await test_cross_document_search()

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
        print("\n🎉 All EDGAR tests passed! Filing ingestion is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
