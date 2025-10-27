"""
Quick report quality test script
Tests 3 different stocks and saves outputs
"""
import asyncio
import json
import time
from datetime import datetime
from backend.agents.graph import create_research_graph

async def test_stock(ticker: str, query: str) -> dict:
    """Test a single stock query"""
    print(f"\n{'='*60}")
    print(f"Testing: {ticker}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    graph = create_research_graph()

    start_time = time.time()

    result = await graph.ainvoke({
        "user_query": query,
        "messages": [],
        "current_agent": "router"
    })

    elapsed = time.time() - start_time

    return {
        "ticker": ticker,
        "query": query,
        "report": result.get("report", "No report generated"),
        "execution_time": round(elapsed, 2),
        "tickers_found": result.get("tickers", []),
        "intent": result.get("intent", "unknown")
    }

async def main():
    """Run all tests"""
    test_queries = [
        ("AAPL", "Give me a research report on AAPL"),
        ("TSLA", "What's the current stock price and outlook for Tesla?"),
        ("GOOGL", "Analyze Google stock for me")
    ]

    results = []

    for ticker, query in test_queries:
        try:
            result = await test_stock(ticker, query)
            results.append(result)
            print(f"\n✅ {ticker} report generated ({result['execution_time']}s)")
            print(f"\nReport Preview (first 500 chars):")
            print(result['report'][:500] + "...\n")
        except Exception as e:
            print(f"\n❌ {ticker} failed: {str(e)}\n")
            results.append({
                "ticker": ticker,
                "query": query,
                "error": str(e)
            })

    # Save results
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Test Complete - Results saved to: {output_file}")
    print(f"{'='*60}\n")

    return results

if __name__ == "__main__":
    asyncio.run(main())
