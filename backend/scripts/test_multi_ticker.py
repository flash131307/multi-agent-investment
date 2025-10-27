"""Quick test for multi-ticker EDGAR ingestion and cross-document search."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.database import MongoDB
from backend.services.chroma_client import chroma_db
from backend.rag.pipeline import rag_pipeline


async def test_multi_ticker_ingestion():
    """Test ingesting multiple tickers."""
    print("="*60)
    print("MULTI-TICKER EDGAR INGESTION")
    print("="*60)

    tickers = ["AAPL", "MSFT", "TSLA"]

    await MongoDB.connect()
    chroma_db.connect()

    results = {}
    for ticker in tickers:
        print(f"\n📥 {ticker}...")
        try:
            count = await rag_pipeline.ingest_edgar_filing(ticker, "10-K", 1)
            results[ticker] = count
            print(f"✅ {ticker}: {count} chunks")
        except Exception as e:
            print(f"❌ {ticker}: {str(e)[:100]}")
            results[ticker] = 0

    total = sum(results.values())
    print(f"\n📊 Total: {total} chunks from {len(tickers)} companies")

    await MongoDB.close()
    return results


async def test_cross_document_search():
    """Test searching across documents."""
    print("\n" + "="*60)
    print("CROSS-DOCUMENT SEARCH")
    print("="*60)

    await MongoDB.connect()
    chroma_db.connect()

    queries = [
        "What are the main business segments?",
        "What are key risk factors?",
        "Revenue growth strategy"
    ]

    for query in queries:
        print(f"\n🔍 {query}")

        results = await rag_pipeline.retrieve_context(
            query=query,
            source="edgar",
            top_k=5
        )

        # Group by ticker
        by_ticker = {}
        for r in results:
            t = r['metadata'].get('ticker', 'Unknown')
            by_ticker[t] = by_ticker.get(t, 0) + 1

        print(f"   Found {len(results)} results: {dict(by_ticker)}")
        if results:
            top = results[0]
            print(f"   Top: {top['metadata'].get('ticker')} - "
                  f"{top['metadata'].get('section')} "
                  f"(sim: {top['similarity']:.3f})")

    await MongoDB.close()


async def main():
    print("\nQUICK MULTI-TICKER TEST\n")

    # Test 1: Multi-ticker ingestion
    results = await test_multi_ticker_ingestion()

    # Test 2: Cross-document search
    if sum(results.values()) > 0:
        await test_cross_document_search()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for ticker, count in results.items():
        print(f"{ticker}: {count} chunks")
    print(f"\nTotal: {sum(results.values())} chunks")
    print("✅ Tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
