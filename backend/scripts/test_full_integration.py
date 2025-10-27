"""
Full Integration Test - Phase 1 through Phase 4
Simplified test focusing on key integration points.
"""
import asyncio
import logging
from datetime import datetime
import sys

# Configure minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_result(check: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅" if passed else "❌"
    print(f"{status} {check}")
    if details:
        print(f"   {details}")


async def test_phase1_database():
    """Test Phase 1: Database connections."""
    print_section("PHASE 1: DATABASE & INFRASTRUCTURE")

    from backend.services.database import mongodb

    results = []

    # Test MongoDB
    try:
        db = await mongodb.get_database()
        collections = await db.list_collection_names()
        print_result("MongoDB connection", True, f"Found {len(collections)} collections")
        results.append(True)
    except Exception as e:
        print_result("MongoDB connection", False, str(e)[:100])
        results.append(False)

    # Test MongoDB write/read
    try:
        test_collection = db['_integration_test']
        test_doc = {"test": "data", "timestamp": datetime.utcnow()}
        result = await test_collection.insert_one(test_doc)
        found = await test_collection.find_one({"_id": result.inserted_id})
        await test_collection.delete_one({"_id": result.inserted_id})
        print_result("MongoDB write/read", found is not None, "Write and read successful")
        results.append(found is not None)
    except Exception as e:
        print_result("MongoDB write/read", False, str(e)[:100])
        results.append(False)

    return all(results)


async def test_phase2_rag_components():
    """Test Phase 2: RAG Pipeline components."""
    print_section("PHASE 2: RAG PIPELINE COMPONENTS")

    results = []

    # Test embeddings
    print(f"🔢 Testing embeddings...")
    try:
        from backend.rag.embeddings import embedding_service

        sample_text = "Apple Inc. reported strong quarterly earnings."
        embedding = await embedding_service.generate_embedding(sample_text)
        if embedding and len(embedding) > 0:
            print_result("Embeddings generation", True, f"Generated {len(embedding)}-dim vector")
            results.append(True)
        else:
            print_result("Embeddings generation", False, "Empty embedding")
            results.append(False)
    except Exception as e:
        print_result("Embeddings generation", False, str(e)[:100])
        results.append(False)

    # Test EDGAR scraper (may be rate limited)
    print(f"📥 Testing EDGAR scraper...")
    try:
        from backend.rag.edgar_scraper import edgar_scraper

        filings = await edgar_scraper.get_company_filings("AAPL", form_types=["10-K"], limit=1)
        if filings and len(filings) > 0:
            print_result("EDGAR API access", True, f"Found {len(filings)} filings")
            results.append(True)
        else:
            print_result("EDGAR API access", False, "No filings (may be rate limited)")
            results.append(False)  # Don't fail the phase for this
    except Exception as e:
        print_result("EDGAR API access", False, str(e)[:100])
        results.append(False)

    # Test RAG pipeline
    print(f"🔍 Testing RAG pipeline...")
    try:
        from backend.rag.pipeline import rag_pipeline

        query = "What are the key financial metrics for AAPL?"
        retrieved = await rag_pipeline.retrieve_context(
            query=query,
            ticker="AAPL",
            top_k=3
        )
        print_result("RAG retrieval", True, f"Retrieved {len(retrieved)} documents")
        results.append(True)
    except Exception as e:
        print_result("RAG retrieval", False, str(e)[:100])
        results.append(False)

    return all(results)


async def test_phase3_data_sources():
    """Test Phase 3: External data sources."""
    print_section("PHASE 3: EXTERNAL DATA SOURCES")

    results = []

    # Test Yahoo Finance
    print(f"📊 Testing Yahoo Finance...")
    try:
        from backend.services.yahoo_finance import yahoo_finance

        stock_info = yahoo_finance.get_stock_info("TSLA")
        if stock_info and stock_info.get('current_price'):
            price = stock_info['current_price']
            mcap = stock_info.get('market_cap', 0)
            print_result(
                "Yahoo Finance API",
                True,
                f"TSLA: ${price}, MCap: ${mcap:,}" if mcap else f"TSLA: ${price}"
            )
            results.append(True)
        else:
            print_result("Yahoo Finance API", False, "No data returned")
            results.append(False)
    except Exception as e:
        print_result("Yahoo Finance API", False, str(e)[:100])
        results.append(False)

    # Test News Aggregator
    print(f"📰 Testing News Aggregator...")
    try:
        from backend.rag.news_aggregator import news_aggregator

        news_summary = news_aggregator.get_news_summary("TSLA", limit=5)
        if news_summary and news_summary.get('news'):
            news_count = len(news_summary['news'])
            print_result("News aggregation", True, f"Found {news_count} articles for TSLA")
            results.append(True)
        else:
            print_result("News aggregation", False, "No news found")
            results.append(False)
    except Exception as e:
        print_result("News aggregation", False, str(e)[:100])
        results.append(False)

    return all(results)


async def test_phase4_agent_workflow():
    """Test Phase 4: Complete multi-agent workflow."""
    print_section("PHASE 4: MULTI-AGENT WORKFLOW")

    from backend.agents.graph import run_research_query
    from backend.memory.conversation import conversation_memory

    results = []

    # Run 2 test cases
    test_cases = [
        {"name": "Price Query", "query": "What's the current stock price of MSFT?"},
        {"name": "Investment Report", "query": "Give me a research report on NVDA"}
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n🤖 Test Case {i}: {test['name']}")
        print(f"   Query: '{test['query']}'")

        try:
            session_id = f"integration_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"

            # Run complete workflow
            final_state = await run_research_query(session_id, test['query'])

            # Validate results
            has_intent = final_state.get('intent') is not None
            has_tickers = len(final_state.get('tickers', [])) > 0
            has_market = len(final_state.get('market_data', [])) > 0
            has_sentiment = len(final_state.get('sentiment_analysis', [])) > 0
            has_report = final_state.get('report') is not None and len(final_state.get('report', '')) > 100

            print_result(f"  Intent: {final_state.get('intent')}", has_intent)
            print_result(f"  Tickers: {final_state.get('tickers')}", has_tickers)
            print_result(f"  Market data", has_market)
            print_result(f"  Sentiment", has_sentiment)
            print_result(f"  Report", has_report, f"{len(final_state.get('report', ''))} chars")

            # Check memory
            saved_msgs = await conversation_memory.get_conversation(session_id)
            memory_ok = len(saved_msgs) >= 2
            print_result(f"  Memory saved", memory_ok, f"{len(saved_msgs)} messages")

            test_passed = all([has_intent, has_tickers, has_report, memory_ok])
            results.append(test_passed)

            if test_passed:
                print(f"✅ Test Case {i} PASSED")
            else:
                print(f"❌ Test Case {i} FAILED")

        except Exception as e:
            print_result(f"  Execution", False, str(e)[:100])
            logger.error(f"Full error: {e}", exc_info=True)
            results.append(False)

    return all(results)


async def run_full_integration_test():
    """Run complete integration test."""
    print("\n" + "=" * 70)
    print("  🚀 FULL SYSTEM INTEGRATION TEST - PHASE 1-4")
    print("=" * 70)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Connect to MongoDB
    print("\n📥 Connecting to databases...")
    from backend.services.database import mongodb

    try:
        await mongodb.connect()
        print("✅ MongoDB connected\n")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        sys.exit(1)

    # Run all tests
    phase_results = {}

    try:
        print("Starting Phase 1...")
        phase_results['Phase 1'] = await test_phase1_database()

        print("\nStarting Phase 2...")
        phase_results['Phase 2'] = await test_phase2_rag_components()

        print("\nStarting Phase 3...")
        phase_results['Phase 3'] = await test_phase3_data_sources()

        print("\nStarting Phase 4...")
        phase_results['Phase 4'] = await test_phase4_agent_workflow()

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        print(f"\n❌ Test suite crashed: {e}")

    # Print summary
    print_section("FINAL SUMMARY")

    total_passed = sum(1 for v in phase_results.values() if v is True)
    total_phases = len(phase_results)

    for phase, passed in phase_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{phase}: {status}")

    print(f"\n{'=' * 70}")
    print(f"  Result: {total_passed}/{total_phases} phases passed")
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

    if total_passed == total_phases:
        print("🎉 ALL TESTS PASSED! System is fully operational.\n")
        sys.exit(0)
    else:
        print(f"⚠️  {total_phases - total_passed} phase(s) failed. See details above.\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_full_integration_test())
