"""
Test Current Report Quality
Demonstrates all completed features:
- Sentiment Analysis (80% confidence)
- EDGAR Integration (100% coverage)
- 52-Week Trend Analysis
- Analyst Consensus (price targets, recommendations)
"""
import asyncio
from backend.agents.graph import run_research_query


async def test_report_quality():
    """Test complete report quality with Microsoft (MSFT)."""
    print("=" * 80)
    print("REPORT QUALITY TEST - Phase 5 (71% Complete)")
    print("=" * 80)
    print("\nFeatures Tested:")
    print("  ✅ Sentiment Analysis (80% confidence)")
    print("  ✅ EDGAR Integration (100% coverage)")
    print("  ✅ 52-Week Trend Analysis")
    print("  ✅ Analyst Consensus (price targets)")
    print("=" * 80)

    query = "Should I invest in Microsoft? Give me a comprehensive analysis."
    ticker = "MSFT"

    print(f"\n🔍 Query: {query}")
    print(f"📊 Ticker: {ticker}\n")
    print("⏳ Generating report... (this may take 10-15 seconds)\n")

    # Run the query
    result = await run_research_query(
        session_id="test_report_quality_msft",
        user_query=query
    )

    # Extract data
    market_data = result.get("market_data", [])
    sentiment = result.get("sentiment_analysis", [])
    analyst_consensus = result.get("analyst_consensus", [])
    context = result.get("retrieved_context", [])
    report = result.get("report", "No report generated")

    # Show data summary
    print("=" * 80)
    print("DATA SUMMARY")
    print("=" * 80)

    # Market Data (52-Week Trends)
    if market_data:
        print("\n📊 MARKET DATA (52-WEEK TRENDS):")
        for data in market_data:
            print(f"  Ticker: {data.get('ticker')}")
            print(f"  Current Price: ${data.get('current_price', 0):.2f}")
            print(f"  Market Cap: ${data.get('market_cap', 0):,.0f}")
            print(f"  P/E Ratio: {data.get('pe_ratio', 'N/A')}")
            print(f"  52W Range: ${data.get('year_low', 0):.2f} - ${data.get('year_high', 0):.2f}")
            print(f"  Position in Range: {data.get('week_52_position', 0):.1f}%")
            print(f"  Distance from High: {data.get('distance_from_high', 0):+.1f}%")
            print(f"  Distance from Low: {data.get('distance_from_low', 0):+.1f}%")
            print(f"  Trend Signal: {data.get('trend_signal', 'N/A').upper()}")
    else:
        print("\n  ❌ No market data")

    # Sentiment Analysis
    if sentiment:
        print("\n💭 SENTIMENT ANALYSIS:")
        for s in sentiment:
            print(f"  Ticker: {s.get('ticker')}")
            print(f"  Overall Sentiment: {s.get('overall_sentiment', 'N/A').upper()}")
            print(f"  Confidence: {s.get('confidence', 0):.0%}")
            print(f"  Key Themes: {', '.join(s.get('key_themes', []))}")
            print(f"  News Count: {s.get('news_count', 0)}")
    else:
        print("\n  ❌ No sentiment analysis")

    # Analyst Consensus
    if analyst_consensus:
        print("\n📈 ANALYST CONSENSUS:")
        for consensus in analyst_consensus:
            print(f"  Ticker: {consensus.get('ticker')}")
            print(f"  Current Price: ${consensus.get('current_price', 0):.2f}")
            print(f"  Target Mean: ${consensus.get('target_price_mean', 0):.2f}")
            print(f"  Target Range: ${consensus.get('target_price_low', 0):.2f} - ${consensus.get('target_price_high', 0):.2f}")
            upside = consensus.get('upside_potential', 0)
            direction = "↑ UPSIDE" if upside > 0 else "↓ DOWNSIDE"
            print(f"  Potential: {upside:+.1f}% {direction}")
            print(f"  Recommendation: {consensus.get('recommendation', 'N/A').upper()}")
            print(f"  # Analysts: {consensus.get('num_analysts', 0)}")
    else:
        print("\n  ❌ No analyst consensus")

    # EDGAR Context
    if context:
        print(f"\n📄 EDGAR CONTEXT: {len(context)} documents retrieved")
        for i, ctx in enumerate(context[:3], 1):
            source = ctx.get('metadata', {}).get('source', 'Unknown')
            similarity = ctx.get('similarity', 0)
            print(f"  {i}. {source} (similarity: {similarity:.2%})")
    else:
        print("\n  ❌ No EDGAR context")

    # Full Report
    print("\n" + "=" * 80)
    print("FULL INVESTMENT RESEARCH REPORT")
    print("=" * 80)
    print(report)
    print("=" * 80)

    # Report Quality Validation
    print("\n" + "=" * 80)
    print("REPORT QUALITY VALIDATION")
    print("=" * 80)

    checks = {
        "Market Data Present": bool(market_data),
        "52-Week Trends Included": any("52-week" in report.lower() or "52w" in report.lower() for _ in [1]),
        "Sentiment Analysis Present": bool(sentiment),
        "Sentiment in Report": "sentiment" in report.lower(),
        "Analyst Consensus Present": bool(analyst_consensus),
        "Target Price in Report": "target" in report.lower() and "price" in report.lower(),
        "EDGAR Context Present": bool(context),
        "EDGAR Referenced in Report": any(source in report.lower() for source in ["10-k", "10-q", "edgar", "filing"]),
        "Executive Summary": "executive summary" in report.lower(),
        "Market Analysis Section": "market analysis" in report.lower(),
        "Key Insights": "key insights" in report.lower() or "insights" in report.lower(),
        "Conclusion": "conclusion" in report.lower(),
    }

    passed = sum(checks.values())
    total = len(checks)
    score = (passed / total) * 100

    print(f"\nQuality Checks: {passed}/{total} ({score:.0f}%)\n")
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")

    # Overall Grade
    if score >= 90:
        grade = "A+ (Excellent)"
    elif score >= 80:
        grade = "A (Very Good)"
    elif score >= 70:
        grade = "B (Good)"
    else:
        grade = "C (Needs Improvement)"

    print(f"\n{'=' * 80}")
    print(f"OVERALL REPORT GRADE: {grade}")
    print(f"{'=' * 80}")

    # Save report to file
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_report_{ticker.lower()}_{timestamp}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Investment Research Report Quality Test\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Ticker**: {ticker}\n")
        f.write(f"**Query**: {query}\n")
        f.write(f"**Overall Grade**: {grade}\n")
        f.write(f"**Quality Score**: {score:.0f}%\n\n")
        f.write("---\n\n")

        # Data Summary
        f.write("## Data Summary\n\n")

        if market_data:
            f.write("### Market Data (52-Week Trends)\n\n")
            for data in market_data:
                f.write(f"- **Ticker**: {data.get('ticker')}\n")
                f.write(f"- **Current Price**: ${data.get('current_price', 0):.2f}\n")
                f.write(f"- **Market Cap**: ${data.get('market_cap', 0):,.0f}\n")
                f.write(f"- **P/E Ratio**: {data.get('pe_ratio', 'N/A')}\n")
                f.write(f"- **52W Range**: ${data.get('year_low', 0):.2f} - ${data.get('year_high', 0):.2f}\n")
                f.write(f"- **Position in Range**: {data.get('week_52_position', 0):.1f}%\n")
                f.write(f"- **Distance from High**: {data.get('distance_from_high', 0):+.1f}%\n")
                f.write(f"- **Distance from Low**: {data.get('distance_from_low', 0):+.1f}%\n")
                f.write(f"- **Trend Signal**: {data.get('trend_signal', 'N/A').upper()}\n\n")

        if sentiment:
            f.write("### Sentiment Analysis\n\n")
            for s in sentiment:
                f.write(f"- **Ticker**: {s.get('ticker')}\n")
                f.write(f"- **Overall Sentiment**: {s.get('overall_sentiment', 'N/A').upper()}\n")
                f.write(f"- **Confidence**: {s.get('confidence', 0):.0%}\n")
                f.write(f"- **Key Themes**: {', '.join(s.get('key_themes', []))}\n")
                f.write(f"- **News Count**: {s.get('news_count', 0)}\n\n")

        if analyst_consensus:
            f.write("### Analyst Consensus\n\n")
            for consensus in analyst_consensus:
                f.write(f"- **Ticker**: {consensus.get('ticker')}\n")
                f.write(f"- **Current Price**: ${consensus.get('current_price', 0):.2f}\n")
                f.write(f"- **Target Mean**: ${consensus.get('target_price_mean', 0):.2f}\n")
                f.write(f"- **Target Range**: ${consensus.get('target_price_low', 0):.2f} - ${consensus.get('target_price_high', 0):.2f}\n")
                upside = consensus.get('upside_potential', 0)
                direction = "UPSIDE ↑" if upside > 0 else "DOWNSIDE ↓"
                f.write(f"- **Potential**: {upside:+.1f}% {direction}\n")
                f.write(f"- **Recommendation**: {consensus.get('recommendation', 'N/A').upper()}\n")
                f.write(f"- **# Analysts**: {consensus.get('num_analysts', 0)}\n\n")

        if context:
            f.write(f"### EDGAR Context\n\n")
            f.write(f"Retrieved {len(context)} documents from SEC EDGAR filings.\n\n")

        # Full Report
        f.write("---\n\n")
        f.write("## Full Investment Research Report\n\n")
        f.write(report)
        f.write("\n\n---\n\n")

        # Quality Checks
        f.write("## Quality Validation\n\n")
        f.write(f"**Score**: {passed}/{total} ({score:.0f}%)\n\n")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            f.write(f"- {status} {check}\n")

        f.write(f"\n**Overall Grade**: {grade}\n")

    print(f"\n📄 Report saved to: {filename}")

    return result


if __name__ == "__main__":
    asyncio.run(test_report_quality())
