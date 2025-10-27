"""
End-to-end test for LangGraph agent workflow.
Tests the complete multi-agent research system.
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.database import MongoDB
from backend.services.chroma_client import chroma_db
from backend.agents.graph import run_research_query


async def test_agent_workflow():
    """Test complete agent workflow with various queries."""
    print("="*60)
    print("LANGGRAPH AGENT WORKFLOW TEST")
    print("="*60)

    # Connect to databases
    print("\n📥 Connecting to databases...")
    await MongoDB.connect()
    chroma_db.connect()
    print("✅ Connected")

    # Test queries
    test_cases = [
        {
            "name": "Price Query",
            "query": "What's the current price of AAPL?",
            "expected_intent": "price_query"
        },
        {
            "name": "Sentiment Analysis",
            "query": "Analyze sentiment for TSLA",
            "expected_intent": "sentiment_analysis"
        },
        {
            "name": "General Research",
            "query": "Give me a full research report on MSFT",
            "expected_intent": "general_research"
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'='*60}")
        print(f"Query: {test['query']}")

        # Create unique session for each test
        session_id = f"test_{uuid.uuid4().hex[:8]}"

        try:
            # Run the query through the agent workflow
            final_state = await run_research_query(session_id, test['query'])

            # Check results
            success = True
            issues = []

            # Verify intent
            actual_intent = final_state.get("intent", "unknown")
            print(f"\n✓ Intent: {actual_intent}")

            # Verify tickers
            tickers = final_state.get("tickers", [])
            print(f"✓ Tickers: {tickers if tickers else 'None'}")

            # Check if agents ran
            has_market = final_state.get("market_data") is not None
            has_sentiment = final_state.get("sentiment_analysis") is not None
            has_context = final_state.get("retrieved_context") is not None

            print(f"✓ Market Data: {'Yes' if has_market else 'No'}")
            print(f"✓ Sentiment: {'Yes' if has_sentiment else 'No'}")
            print(f"✓ Context: {'Yes' if has_context else 'No'}")

            # Check report
            report = final_state.get("report")
            if report:
                print(f"✓ Report: {len(report)} characters")
                print(f"\n📄 Report Preview:")
                print("-" * 60)
                print(report[:500] + "..." if len(report) > 500 else report)
                print("-" * 60)
            else:
                success = False
                issues.append("No report generated")
                print("✗ Report: Missing")

            # Check errors
            errors = final_state.get("errors", [])
            if errors:
                success = False
                print(f"\n⚠️  Errors encountered:")
                for error in errors:
                    print(f"  - {error}")
                    issues.append(error)

            # Summary
            if success:
                print(f"\n✅ TEST {i} PASSED")
            else:
                print(f"\n❌ TEST {i} FAILED")
                for issue in issues:
                    print(f"  - {issue}")

            results.append({
                "test": test['name'],
                "success": success,
                "issues": issues
            })

        except Exception as e:
            print(f"\n❌ TEST {i} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()

            results.append({
                "test": test['name'],
                "success": False,
                "issues": [str(e)]
            })

    # Final summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    for i, result in enumerate(results, 1):
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{i}. {result['test']}: {status}")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"   - {issue}")

    print(f"\nTotal: {passed}/{total} tests passed")

    # Close connections
    await MongoDB.close()

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(test_agent_workflow())
    sys.exit(0 if success else 1)
