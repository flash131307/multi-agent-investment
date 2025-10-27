# Multi-Agent Investment Research Platform - Implementation Plan

**Project Name**: DeepResearch AI
**Tagline**: AI-Powered Deep Equity Research with Traceable Insights
**Version**: 2.0 (Optimized after ValueCell Analysis)

---

## 🎯 Project Repositioning

### Core Positioning

**What We Are**: An AI-driven deep equity research platform that provides institutional-grade analysis with full traceability to source documents.

**What We Are NOT**: A day-trading decision tool (that's ValueCell's domain).

### Value Proposition vs ValueCell

| Dimension | ValueCell | DeepResearch AI (Our Project) |
|-----------|-----------|-------------------------------|
| **User Question** | "What should I buy today?" | "Is this company worth long-term investment? Why?" |
| **Response Time** | 10-30 seconds (fast) | 1-3 minutes (deep) |
| **Output Format** | Brief recommendation + data points | Structured research report + citations |
| **Data Depth** | Real-time + shallow history | 5-year history + deep parsing |
| **Traceability** | ❌ No source verification | ✅ Every claim has a source |
| **Learning Value** | ❌ Conclusions only | ✅ Explains analysis logic |
| **Historical Comparison** | ❌ None | ✅ "What did we think 6 months ago?" |
| **Use Case** | Intraday/short-term trading | Long-term investment decisions |
| **Target Users** | Retail traders | Value investors, analysts, students |
| **Moat** | Multi-market coverage | Deep RAG + Knowledge Graph |

### Target Users

1. **Value Investors**: Need deep research before making investment decisions
2. **Equity Analysts**: Require cited sources for research reports
3. **MBA/CFA Students**: Want to learn analysis methodologies
4. **Institutional Investors**: Need audit trails for compliance

---

## 🚀 5 Key Differentiation Features

### 1. Clickable Citation System

**User Experience**:
```
Output: "AAPL revenue grew 3.2% [¹]"
User clicks [¹] → Modal window shows:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Source: SEC 10-K 2023
  Page: 23
  Section: MD&A, Paragraph 2
  Original Text: "Net sales increased 3.2%..."
  [View Full Document] [Add to Notes]
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Technical Implementation**:
- MongoDB stores: `{claim_id, source_doc, page, section, paragraph, original_text}`
- Frontend renders `[¹]` as clickable link
- API endpoint: `GET /api/citations/{claim_id}`

---

### 2. Comparison View (Multi-Company)

**User Experience**:
```
User: "Compare AAPL and MSFT growth potential"

System outputs side-by-side comparison:
┌──────────────┬─────────┬─────────┐
│   Metric     │  AAPL   │  MSFT   │
├──────────────┼─────────┼─────────┤
│ Revenue Growth│  3.2%   │  7.8%   │✅
│ Net Margin   │  25.3%  │  36.7%  │✅
│ P/E Ratio    │  28.5x  │  32.1x  │
│ AI Rating    │  Hold   │  Buy    │✅
└──────────────┴─────────┴─────────┘

[View Detailed Analysis] [Add More Companies]
```

**Technical Implementation**:
- API endpoint: `POST /api/compare` with `{tickers: ["AAPL", "MSFT"]}`
- Parallel agent execution for each ticker
- Result aggregation and normalization

---

### 3. Time Travel (Historical Analysis)

**User Experience**:
```
User: "What was your analysis of AAPL 6 months ago?"

System shows:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 2024-04-21 Analysis:
Rating: Buy | Target: $180
Reason: Strong iPhone 15 demand

📅 2024-10-22 Analysis (Current):
Rating: Hold | Target: $185
Reason: Growth slowing, but services growing

📊 Trend Changes:
- Revenue growth: 7.8% → 3.2% (declining)
- Services mix: 18% → 22% (improving) ✅

[View Full History] [Play Timeline Animation]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Technical Implementation**:
- MongoDB stores versioned analysis: `{ticker, analysis_date, rating, reasoning, metrics}`
- API endpoint: `GET /api/history/{ticker}?from_date=2024-04-21`
- Frontend timeline component

---

### 4. Knowledge Graph Visualization

**User Experience**:
```
User: "What are AAPL's supply chain risks?"

System displays interactive graph:

          [China Market]
               ↓ 30% revenue
           [AAPL] ←───────── [TSMC] (chips)
             ↓                  ↑
          [Foxconn]       [Taiwan Geopolitical Risk]
             ↓
        [Assembly Risk]

[Click any node for details]
[Export Supply Chain Risk Report]
```

**Technical Implementation**:
- MongoDB stores entity relationships: `{entity_a, relationship_type, entity_b, strength, metadata}`
- Graph query API: `GET /api/graph/{ticker}/supply_chain`
- Frontend uses D3.js or React Flow for visualization

---

### 5. Interactive Valuation Calculator

**User Experience**:
```
User: "If AAPL growth rate increases to 5%, what's fair value?"

System shows adjustable calculator:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
DCF Valuation Model
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Revenue Growth: [━━●━━━━] 5.0%
Net Margin:     [━━━●━━━] 25.3%
WACC:           [━━●━━━━] 8.5%

→ Calculated Target: $198

[View Calculation Details] [Save Scenario]
[Compare with Wall Street Estimates]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Technical Implementation**:
- Backend DCF calculation service
- API endpoint: `POST /api/valuation/dcf` with adjustable parameters
- Real-time recalculation on slider change

---

## 📋 Revised Implementation Plan (Phase 2-8)

### Phase 2: MongoDB Infrastructure + Knowledge Graph (3-4 days)

**Core Objectives**:
1. Establish MongoDB connection with Motor (async driver)
2. Implement dual-memory system (conversation + entity graph)
3. Add citation tracking schema
4. Create vector search indexes

**Database Schemas**:

**A. Conversation Memory (Short-term)**
```javascript
{
  session_id: "uuid",
  user_id: "uuid",
  messages: [
    {
      role: "user",
      content: "...",
      timestamp: ISODate()
    },
    {
      role: "assistant",
      content: "...",
      citations: ["cite_001", "cite_002"],  // NEW
      timestamp: ISODate()
    }
  ],
  created_at: ISODate(),
  ttl_index: 24h
}
```

**B. Entity Graph (Long-term)**
```javascript
{
  entity_id: "AAPL",
  entity_type: "stock",
  name: "Apple Inc.",
  relationships: [
    {
      related_to: "TECH_SECTOR",
      relation_type: "belongs_to",
      strength: 1.0
    },
    {
      related_to: "TSMC",
      relation_type: "supplier",
      strength: 0.8,
      metadata: {description: "Chip supplier"}
    }
  ],
  financial_metrics: {
    revenue: [{value: 383B, date: "2024-Q2"}],
    pe_ratio: [{value: 28.5, date: "2024-Q2"}]
  },
  embedding: [0.123, -0.456, ...],
  last_updated: ISODate()
}
```

**C. Citation Store (NEW)**
```javascript
{
  citation_id: "cite_001",
  source_type: "SEC_10K",
  ticker: "AAPL",
  filing_date: "2024-02-15",
  document_url: "https://sec.gov/...",
  page_number: 23,
  section: "MD&A",
  paragraph_index: 2,
  original_text: "Net sales increased 3.2%...",
  claim_text: "AAPL revenue grew 3.2%",
  embedding: [0.234, -0.567, ...],
  created_at: ISODate()
}
```

**D. Vector Documents**
```javascript
{
  doc_id: "uuid",
  ticker: "AAPL",
  source: "SEC_10K",
  doc_type: "MD&A",
  filing_date: "2024-02-15",
  chunk_text: "...",
  chunk_index: 5,
  metadata: {
    page: 23,
    section: "MD&A",
    paragraph: 2
  },
  embedding: [0.123, -0.456, ...],
  indexed_at: ISODate()
}
```

**E. Historical Analysis (NEW - for Time Travel)**
```javascript
{
  analysis_id: "uuid",
  ticker: "AAPL",
  analysis_date: "2024-04-21",
  rating: "Buy",
  target_price: 180,
  reasoning: "Strong iPhone 15 demand",
  key_metrics: {
    revenue_growth: 7.8,
    pe_ratio: 26.3
  },
  citations: ["cite_005", "cite_006"],
  analyst_agent: "report_generator_v1.0"
}
```

**Files to Create**:
- `backend/memory/mongo_connection.py` - MongoDB async connection
- `backend/memory/conversation.py` - Conversation memory CRUD
- `backend/memory/entity_graph.py` - Entity relationship management
- `backend/memory/citation_store.py` - Citation tracking (NEW)
- `backend/memory/vector_store.py` - Vector operations
- `backend/memory/historical_analysis.py` - Analysis versioning (NEW)
- `backend/scripts/init_db.py` - Database initialization

**Vector Search Index Configuration**:
```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 1536,
        "similarity": "cosine"
      },
      "ticker": {"type": "token"},
      "doc_type": {"type": "token"},
      "filing_date": {"type": "date"}
    }
  }
}
```

**Validation Criteria**:
- ✅ MongoDB connection establishes successfully
- ✅ Can insert/retrieve conversation messages
- ✅ Can create entity relationships
- ✅ Can store and retrieve citations with metadata
- ✅ Vector search returns relevant documents
- ✅ Historical analyses can be queried by date range

---

### Phase 3: Deep RAG Pipeline (4-5 days)

**Core Objectives**:
1. Structured SEC document parsing (not just chunking)
2. Yahoo Finance integration with time-series storage
3. Financial news aggregation with sentiment
4. Hybrid search (vector + metadata + time decay)
5. Citation extraction and linking

**A. SEC EDGAR Deep Parser**

`backend/rag/edgar_parser.py`:
```python
class SECParser:
    def parse_10k(self, filing_url):
        """
        Returns structured document instead of flat chunks
        """
        return {
            "metadata": {...},
            "sections": {
                "business": {
                    "text": "...",
                    "page_range": (5, 15),
                    "key_points": [...]
                },
                "risk_factors": {
                    "text": "...",
                    "page_range": (16, 25),
                    "risks": [
                        {
                            "title": "...",
                            "description": "...",
                            "page": 17
                        }
                    ]
                },
                "md_and_a": {
                    "text": "...",
                    "page_range": (26, 45),
                    "financial_highlights": [...]
                },
                "financial_statements": {
                    "balance_sheet": {...},
                    "income_statement": {...},
                    "cash_flow": {...}
                }
            }
        }
```

**B. Intelligent Chunking with Context**

```python
class ContextualChunker:
    def chunk_with_citation(self, section_data):
        """
        Each chunk knows its exact location in source document
        """
        chunks = []
        for paragraph_idx, para in enumerate(section_data['paragraphs']):
            chunks.append({
                "text": para.text,
                "citation": {
                    "section": section_data['section_name'],
                    "page": para.page_number,
                    "paragraph_index": paragraph_idx,
                    "source_doc": section_data['filing_url']
                }
            })
        return chunks
```

**C. Hybrid Search Implementation**

```python
class HybridSearch:
    async def search(self, query, ticker=None, filters={}):
        """
        Combines:
        1. Vector similarity
        2. Metadata filtering (date, ticker, doc_type)
        3. Time decay (newer docs ranked higher)
        4. Section importance weighting
        """
        # Step 1: Vector search (top 20)
        vector_results = await self.vector_search(query, limit=20)

        # Step 2: Metadata filtering
        filtered = self.filter_by_metadata(
            vector_results,
            ticker=ticker,
            date_range=filters.get('date_range'),
            doc_types=filters.get('doc_types')
        )

        # Step 3: Re-rank with time decay
        reranked = self.apply_time_decay(filtered)

        # Step 4: Section importance boost
        final = self.boost_by_section(reranked, {
            "risk_factors": 1.2,
            "md_and_a": 1.3,
            "business": 1.0
        })

        return final[:5]  # Top 5
```

**D. Citation Extractor**

```python
class CitationExtractor:
    def extract_citation_from_chunk(self, chunk, claim_text):
        """
        Creates citation object linking AI claim to source
        """
        return {
            "citation_id": generate_uuid(),
            "source_type": chunk.metadata.doc_type,
            "ticker": chunk.metadata.ticker,
            "filing_date": chunk.metadata.filing_date,
            "document_url": chunk.metadata.source_url,
            "page_number": chunk.citation.page,
            "section": chunk.citation.section,
            "paragraph_index": chunk.citation.paragraph_index,
            "original_text": chunk.text,
            "claim_text": claim_text,
            "confidence": self.calculate_confidence(chunk, claim_text)
        }
```

**Files to Create**:
- `backend/rag/edgar_scraper.py` - SEC filing downloader
- `backend/rag/edgar_parser.py` - Structured 10-K/10-Q parser (NEW)
- `backend/rag/yahoo_finance.py` - Market data API wrapper
- `backend/rag/news_aggregator.py` - Financial news scraper
- `backend/rag/embeddings.py` - OpenAI embedding generation
- `backend/rag/chunker.py` - Contextual chunking with citations (NEW)
- `backend/rag/hybrid_search.py` - Hybrid retrieval engine (NEW)
- `backend/rag/citation_extractor.py` - Citation generation (NEW)

**Validation Criteria**:
- ✅ Can download and parse 10-K into structured sections
- ✅ Can identify risk factors, MD&A, financial statements
- ✅ Chunks include page/section/paragraph metadata
- ✅ Hybrid search returns more relevant results than pure vector search
- ✅ Every retrieved chunk can generate a citation object

---

### Phase 4: Multi-Agent System with Specialized Analysts (5-6 days)

**Core Objectives**:
1. Implement 5 specialized agents (vs original 3)
2. Add citation generation to each agent
3. Implement agent state with source tracking
4. Build LangGraph workflow with conditional routing

**Agent Architecture**:

**Shared State Schema**:
```python
from typing import TypedDict, List, Dict

class AgentState(TypedDict):
    user_query: str
    ticker: str
    agent_outputs: Dict[str, any]
    citations: List[str]  # NEW: Citation IDs
    intermediate_data: Dict
    final_report: str
```

**1. Market Data Analyst Agent**

`backend/agents/market_data_agent.py`:
```python
class MarketDataAgent:
    async def analyze(self, state: AgentState) -> AgentState:
        ticker = state['ticker']

        # Fetch historical data
        price_data = await self.yahoo_finance.get_historical(ticker, years=5)
        fundamentals = await self.yahoo_finance.get_fundamentals(ticker)

        # Generate analysis with citations
        analysis = {
            "current_price": price_data.latest,
            "price_change_1y": self.calculate_change(price_data, "1Y"),
            "pe_ratio": fundamentals.pe_ratio,
            "revenue_trend": self.analyze_revenue_trend(fundamentals),
            "citations": []  # Yahoo Finance doesn't need citations
        }

        state['agent_outputs']['market_data'] = analysis
        return state
```

**2. SEC Fundamentals Analyst Agent (ENHANCED)**

`backend/agents/fundamentals_agent.py`:
```python
class FundamentalsAgent:
    async def analyze(self, state: AgentState) -> AgentState:
        ticker = state['ticker']

        # Retrieve 10-K documents with RAG
        query = f"Financial performance and business overview for {ticker}"
        relevant_chunks = await self.rag_search(query, ticker=ticker)

        # Extract key metrics WITH citations
        revenue_analysis = await self.extract_revenue_analysis(relevant_chunks)
        risk_factors = await self.extract_risks(relevant_chunks)

        # Generate citations for each claim
        citations = []
        for chunk in relevant_chunks:
            citation = self.citation_extractor.extract(
                chunk,
                claim_text=revenue_analysis['claim']
            )
            citations.append(citation['citation_id'])
            await self.citation_store.save(citation)

        state['agent_outputs']['fundamentals'] = {
            "revenue_analysis": revenue_analysis,
            "risk_factors": risk_factors,
            "citations": citations  # NEW
        }
        state['citations'].extend(citations)

        return state
```

**3. News & Sentiment Analyzer Agent**

`backend/agents/sentiment_agent.py`:
```python
class SentimentAgent:
    async def analyze(self, state: AgentState) -> AgentState:
        ticker = state['ticker']

        # Fetch recent news
        news_articles = await self.news_aggregator.fetch(ticker, days=30)

        # Sentiment analysis
        sentiment_scores = []
        key_events = []

        for article in news_articles:
            score = await self.analyze_sentiment(article.content)
            sentiment_scores.append(score)

            if score.magnitude > 0.7:  # Significant event
                key_events.append({
                    "date": article.published_date,
                    "headline": article.title,
                    "sentiment": score.polarity,
                    "source": article.source
                })

        state['agent_outputs']['sentiment'] = {
            "overall_sentiment": np.mean([s.polarity for s in sentiment_scores]),
            "positive_ratio": len([s for s in sentiment_scores if s.polarity > 0]) / len(sentiment_scores),
            "key_events": key_events,
            "news_count": len(news_articles)
        }

        return state
```

**4. Valuation Agent (NEW)**

`backend/agents/valuation_agent.py`:
```python
class ValuationAgent:
    async def analyze(self, state: AgentState) -> AgentState:
        ticker = state['ticker']
        fundamentals = state['agent_outputs']['fundamentals']
        market_data = state['agent_outputs']['market_data']

        # DCF Valuation
        dcf_value = await self.calculate_dcf(
            revenue=fundamentals['revenue_analysis']['current'],
            growth_rate=fundamentals['revenue_analysis']['cagr_5y'],
            margin=fundamentals['net_margin'],
            wacc=self.estimate_wacc(ticker)
        )

        # Comparable Company Analysis
        peers = await self.find_peer_companies(ticker)
        peer_multiples = await self.calculate_peer_multiples(peers)
        comps_value = self.apply_multiples(market_data, peer_multiples)

        # Historical Valuation Analysis
        historical_pe = await self.get_historical_pe(ticker, years=5)

        state['agent_outputs']['valuation'] = {
            "dcf_target": dcf_value,
            "comps_target": comps_value,
            "average_target": (dcf_value + comps_value) / 2,
            "current_price": market_data['current_price'],
            "upside_potential": ((dcf_value + comps_value) / 2) / market_data['current_price'] - 1,
            "historical_pe_percentile": self.calculate_percentile(
                market_data['pe_ratio'],
                historical_pe
            )
        }

        return state
```

**5. Competitive Analysis Agent (NEW)**

`backend/agents/competitive_agent.py`:
```python
class CompetitiveAgent:
    async def analyze(self, state: AgentState) -> AgentState:
        ticker = state['ticker']

        # Find competitors
        competitors = await self.find_competitors(ticker)

        # Fetch metrics for all
        comparison_data = {}
        for comp_ticker in [ticker] + competitors:
            comparison_data[comp_ticker] = await self.fetch_key_metrics(comp_ticker)

        # Rank by various metrics
        rankings = {
            "revenue_growth": self.rank_by_metric(comparison_data, 'revenue_growth'),
            "margins": self.rank_by_metric(comparison_data, 'net_margin'),
            "valuation": self.rank_by_metric(comparison_data, 'pe_ratio', ascending=True),
            "market_share": self.estimate_market_share(comparison_data)
        }

        state['agent_outputs']['competitive'] = {
            "competitors": competitors,
            "comparison_table": comparison_data,
            "rankings": rankings,
            "competitive_position": self.assess_position(ticker, rankings)
        }

        return state
```

**6. Report Generator Agent (ENHANCED)**

`backend/agents/report_agent.py`:
```python
class ReportAgent:
    async def generate_report(self, state: AgentState) -> AgentState:
        # Gather all agent outputs
        market = state['agent_outputs']['market_data']
        fundamentals = state['agent_outputs']['fundamentals']
        sentiment = state['agent_outputs']['sentiment']
        valuation = state['agent_outputs']['valuation']
        competitive = state['agent_outputs']['competitive']

        # Generate structured report with embedded citations
        report = await self.llm.generate(
            template=self.REPORT_TEMPLATE,
            context={
                "ticker": state['ticker'],
                "market_data": market,
                "fundamentals": fundamentals,
                "sentiment": sentiment,
                "valuation": valuation,
                "competitive": competitive
            }
        )

        # Parse report and link citations
        parsed_report = self.parse_and_link_citations(
            report,
            state['citations']
        )

        state['final_report'] = parsed_report
        return state
```

**LangGraph Workflow**:

`backend/agents/router.py`:
```python
from langgraph.graph import StateGraph, END

def create_research_workflow():
    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node("market_data", market_data_agent.analyze)
    workflow.add_node("fundamentals", fundamentals_agent.analyze)
    workflow.add_node("sentiment", sentiment_agent.analyze)
    workflow.add_node("valuation", valuation_agent.analyze)
    workflow.add_node("competitive", competitive_agent.analyze)
    workflow.add_node("report", report_agent.generate_report)

    # Define workflow
    workflow.set_entry_point("market_data")

    # Parallel execution of fundamentals and sentiment
    workflow.add_edge("market_data", "fundamentals")
    workflow.add_edge("market_data", "sentiment")

    # Valuation depends on fundamentals
    workflow.add_edge("fundamentals", "valuation")

    # Competitive runs after fundamentals
    workflow.add_edge("fundamentals", "competitive")

    # Report waits for all
    workflow.add_conditional_edges(
        "valuation",
        lambda s: "report" if all_agents_complete(s) else "wait",
        {"report": "report", "wait": "wait"}
    )

    workflow.add_edge("report", END)

    return workflow.compile()
```

**Files to Create**:
- `backend/agents/base_agent.py` - Base class with citation support
- `backend/agents/router.py` - LangGraph workflow definition
- `backend/agents/market_data_agent.py` - Market data analysis
- `backend/agents/fundamentals_agent.py` - SEC filing analysis (enhanced)
- `backend/agents/sentiment_agent.py` - News sentiment analysis
- `backend/agents/valuation_agent.py` - DCF & comps valuation (NEW)
- `backend/agents/competitive_agent.py` - Peer comparison (NEW)
- `backend/agents/report_agent.py` - Report synthesis (enhanced)
- `backend/agents/state_models.py` - Pydantic state definitions

**Validation Criteria**:
- ✅ All 5 agents execute successfully
- ✅ Citations are generated and stored for fundamental claims
- ✅ Valuation agent produces DCF and comps targets
- ✅ Competitive agent ranks company vs peers
- ✅ Report includes properly formatted citation markers [¹] [²]
- ✅ Workflow handles parallel agent execution

---

### Phase 5: FastAPI Backend with Enhanced APIs (3-4 days)

**Core Objectives**:
1. Implement research report generation endpoint
2. Add citation retrieval API (NEW)
3. Add company comparison API (NEW)
4. Add historical analysis API (NEW - Time Travel)
5. Add knowledge graph API (NEW)
6. Implement WebSocket streaming

**API Endpoints**:

**A. Research Report Generation**

```python
# backend/api/routes/research.py

@router.post("/api/research/generate")
async def generate_research_report(request: ResearchRequest):
    """
    Generate comprehensive research report for a ticker

    Request:
    {
        "ticker": "AAPL",
        "depth": "full",  # or "quick"
        "include_comparison": false
    }

    Response:
    {
        "report_id": "uuid",
        "ticker": "AAPL",
        "generated_at": "2024-10-22T10:30:00Z",
        "rating": "Hold",
        "target_price": 185.0,
        "report": {
            "executive_summary": "...",
            "financial_analysis": "...",
            "valuation": "...",
            "risks": "...",
            "recommendation": "..."
        },
        "citations": ["cite_001", "cite_002", ...],
        "metrics": {...}
    }
    """
    # Execute agent workflow
    result = await research_workflow.run({"ticker": request.ticker})

    # Save to historical analysis
    await historical_analysis_store.save(result)

    return result
```

**B. Citation Retrieval API (NEW)**

```python
@router.get("/api/citations/{citation_id}")
async def get_citation(citation_id: str):
    """
    Retrieve detailed citation information

    Response:
    {
        "citation_id": "cite_001",
        "source_type": "SEC_10K",
        "ticker": "AAPL",
        "filing_date": "2024-02-15",
        "document_url": "https://sec.gov/...",
        "page_number": 23,
        "section": "MD&A",
        "paragraph_index": 2,
        "original_text": "Net sales increased 3.2%...",
        "claim_text": "AAPL revenue grew 3.2%",
        "context_before": "...",
        "context_after": "..."
    }
    """
    return await citation_store.get(citation_id)
```

**C. Company Comparison API (NEW)**

```python
@router.post("/api/compare")
async def compare_companies(request: CompareRequest):
    """
    Compare multiple companies side-by-side

    Request:
    {
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "metrics": ["revenue_growth", "net_margin", "pe_ratio", "ai_rating"]
    }

    Response:
    {
        "comparison_id": "uuid",
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "metrics": {
            "revenue_growth": {
                "AAPL": 3.2,
                "MSFT": 7.8,
                "GOOGL": 9.1
            },
            "net_margin": {...},
            "ai_rating": {
                "AAPL": "Hold",
                "MSFT": "Buy",
                "GOOGL": "Buy"
            }
        },
        "analysis": "..."
    }
    """
    # Run agents in parallel for all tickers
    results = await asyncio.gather(*[
        research_workflow.run({"ticker": t}) for t in request.tickers
    ])

    # Aggregate and normalize
    comparison = aggregate_results(results, request.metrics)

    return comparison
```

**D. Historical Analysis API (NEW - Time Travel)**

```python
@router.get("/api/history/{ticker}")
async def get_historical_analysis(
    ticker: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """
    Retrieve historical analyses for a ticker

    Response:
    {
        "ticker": "AAPL",
        "analyses": [
            {
                "date": "2024-04-21",
                "rating": "Buy",
                "target_price": 180,
                "key_metrics": {...},
                "citations": [...]
            },
            {
                "date": "2024-10-22",
                "rating": "Hold",
                "target_price": 185,
                "key_metrics": {...},
                "citations": [...]
            }
        ],
        "trend_analysis": {
            "rating_changes": [...],
            "metric_trends": {...}
        }
    }
    """
    return await historical_analysis_store.get_history(
        ticker,
        from_date,
        to_date
    )
```

**E. Knowledge Graph API (NEW)**

```python
@router.get("/api/graph/{ticker}/{relationship_type}")
async def get_knowledge_graph(
    ticker: str,
    relationship_type: str  # "supply_chain", "competitors", "all"
):
    """
    Retrieve entity relationship graph

    Response:
    {
        "ticker": "AAPL",
        "graph": {
            "nodes": [
                {"id": "AAPL", "type": "stock", "name": "Apple Inc."},
                {"id": "TSMC", "type": "supplier", "name": "Taiwan Semiconductor"},
                {"id": "CHINA_MARKET", "type": "market", "name": "China Market"}
            ],
            "edges": [
                {"from": "AAPL", "to": "TSMC", "type": "supplier", "strength": 0.8},
                {"from": "AAPL", "to": "CHINA_MARKET", "type": "revenue_source", "strength": 0.3}
            ]
        }
    }
    """
    return await entity_graph_store.get_subgraph(ticker, relationship_type)
```

**F. WebSocket Streaming**

```python
# backend/api/websocket.py

@app.websocket("/ws/research/{ticker}")
async def websocket_research(websocket: WebSocket, ticker: str):
    await websocket.accept()

    try:
        # Stream agent progress
        async for event in research_workflow.stream({"ticker": ticker}):
            await websocket.send_json({
                "type": "progress",
                "agent": event.agent_name,
                "status": event.status,
                "data": event.data
            })

        # Send final report
        await websocket.send_json({
            "type": "complete",
            "report": event.final_report
        })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {ticker}")
```

**Files to Create**:
- `backend/api/routes/research.py` - Research endpoints
- `backend/api/routes/citations.py` - Citation API (NEW)
- `backend/api/routes/comparison.py` - Company comparison (NEW)
- `backend/api/routes/history.py` - Historical analysis (NEW)
- `backend/api/routes/graph.py` - Knowledge graph (NEW)
- `backend/api/websocket.py` - WebSocket streaming (enhanced)
- `backend/api/models.py` - Pydantic request/response models

**Validation Criteria**:
- ✅ `/api/research/generate` returns complete report with citations
- ✅ `/api/citations/{id}` retrieves full citation details
- ✅ `/api/compare` handles 2-5 companies comparison
- ✅ `/api/history/{ticker}` returns time-series analysis
- ✅ `/api/graph/{ticker}/*` returns graph data
- ✅ WebSocket streams agent progress in real-time

---

### Phase 6: Groq Integration (2-3 days)

**Core Objectives**:
1. Implement Groq API client with streaming
2. Add streaming over WebSocket
3. Implement error handling and rate limiting

*This phase remains largely unchanged from original plan*

**Files to Create**:
- `backend/services/groq_client.py` - Groq API integration
- `backend/services/llm_providers.py` - Abstract LLM interface

**Validation Criteria**:
- ✅ Groq streaming works via WebSocket
- ✅ Rate limiting handles 30 req/min limit
- ✅ Graceful fallback on errors

---

### Phase 7: Frontend Dashboard (5-7 days)

**Core Objectives**:
1. Build React app with WebSocket client
2. Implement Citation Viewer component (NEW)
3. Implement Comparison View component (NEW)
4. Implement Time Travel Timeline component (NEW)
5. Implement Knowledge Graph Visualization (NEW)
6. Implement Interactive Valuation Calculator (NEW)
7. Basic portfolio tracking

**Key Components**:

**A. Citation Viewer Component (NEW)**

```tsx
// frontend/src/components/CitationViewer.tsx

interface Citation {
  id: string;
  sourceType: string;
  ticker: string;
  pageNumber: number;
  section: string;
  originalText: string;
  claimText: string;
}

function CitationViewer({ citationId }: { citationId: string }) {
  const [citation, setCitation] = useState<Citation | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const fetchCitation = async () => {
    const res = await fetch(`/api/citations/${citationId}`);
    setCitation(await res.json());
    setIsOpen(true);
  };

  return (
    <>
      <sup
        className="citation-link"
        onClick={fetchCitation}
      >
        [¹]
      </sup>

      {isOpen && (
        <Modal>
          <div className="citation-details">
            <h3>Source: {citation.sourceType}</h3>
            <p>Page: {citation.pageNumber} | Section: {citation.section}</p>
            <blockquote>{citation.originalText}</blockquote>
            <button>View Full Document</button>
          </div>
        </Modal>
      )}
    </>
  );
}
```

**B. Comparison Table Component (NEW)**

```tsx
// frontend/src/components/ComparisonTable.tsx

function ComparisonTable({ tickers }: { tickers: string[] }) {
  const [comparisonData, setComparisonData] = useState(null);

  useEffect(() => {
    fetch('/api/compare', {
      method: 'POST',
      body: JSON.stringify({ tickers })
    }).then(res => res.json())
      .then(setComparisonData);
  }, [tickers]);

  return (
    <table className="comparison-table">
      <thead>
        <tr>
          <th>Metric</th>
          {tickers.map(t => <th key={t}>{t}</th>)}
        </tr>
      </thead>
      <tbody>
        {Object.entries(comparisonData?.metrics || {}).map(([metric, values]) => (
          <tr key={metric}>
            <td>{metric}</td>
            {tickers.map(t => (
              <td key={t}>
                {values[t]}
                {getBestValue(values) === values[t] && <span>✅</span>}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

**C. Time Travel Timeline (NEW)**

```tsx
// frontend/src/components/TimeTravel.tsx

function TimeTravelTimeline({ ticker }: { ticker: string }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetch(`/api/history/${ticker}`)
      .then(res => res.json())
      .then(data => setHistory(data.analyses));
  }, [ticker]);

  return (
    <div className="timeline">
      {history.map((analysis, idx) => (
        <div key={idx} className="timeline-item">
          <div className="date">{analysis.date}</div>
          <div className="rating">{analysis.rating}</div>
          <div className="target">${analysis.target_price}</div>
          <button onClick={() => showDetails(analysis)}>
            View Full Analysis
          </button>
        </div>
      ))}

      <div className="trend-chart">
        <LineChart data={extractTrends(history)} />
      </div>
    </div>
  );
}
```

**D. Knowledge Graph Visualization (NEW)**

```tsx
// frontend/src/components/KnowledgeGraph.tsx

import ReactFlow from 'reactflow';

function KnowledgeGraph({ ticker }: { ticker: string }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  useEffect(() => {
    fetch(`/api/graph/${ticker}/all`)
      .then(res => res.json())
      .then(data => setGraphData(convertToReactFlow(data.graph)));
  }, [ticker]);

  return (
    <div style={{ height: '600px' }}>
      <ReactFlow
        nodes={graphData.nodes}
        edges={graphData.edges}
        onNodeClick={(event, node) => showNodeDetails(node)}
      />
    </div>
  );
}
```

**E. Interactive Valuation Calculator (NEW)**

```tsx
// frontend/src/components/ValuationCalculator.tsx

function ValuationCalculator({ ticker }: { ticker: string }) {
  const [params, setParams] = useState({
    revenueGrowth: 5.0,
    netMargin: 25.3,
    wacc: 8.5
  });
  const [targetPrice, setTargetPrice] = useState(null);

  const recalculate = async () => {
    const res = await fetch('/api/valuation/dcf', {
      method: 'POST',
      body: JSON.stringify({ ticker, ...params })
    });
    const data = await res.json();
    setTargetPrice(data.target_price);
  };

  return (
    <div className="valuation-calculator">
      <h3>DCF Valuation Model</h3>

      <div className="slider-group">
        <label>Revenue Growth: {params.revenueGrowth}%</label>
        <input
          type="range"
          min="0"
          max="20"
          step="0.1"
          value={params.revenueGrowth}
          onChange={(e) => {
            setParams({...params, revenueGrowth: e.target.value});
            recalculate();
          }}
        />
      </div>

      {/* Similar sliders for netMargin and wacc */}

      <div className="result">
        <h2>Calculated Target: ${targetPrice}</h2>
      </div>

      <button>Save Scenario</button>
      <button>Compare with Wall Street</button>
    </div>
  );
}
```

**Files to Create**:
- `frontend/src/App.tsx` - Main application
- `frontend/src/components/ResearchReport.tsx` - Report display
- `frontend/src/components/CitationViewer.tsx` - Citation modal (NEW)
- `frontend/src/components/ComparisonTable.tsx` - Multi-company comparison (NEW)
- `frontend/src/components/TimeTravel.tsx` - Historical timeline (NEW)
- `frontend/src/components/KnowledgeGraph.tsx` - Graph visualization (NEW)
- `frontend/src/components/ValuationCalculator.tsx` - DCF calculator (NEW)
- `frontend/src/services/websocket.ts` - WebSocket client
- `frontend/src/services/api.ts` - API client

**Validation Criteria**:
- ✅ Can generate and display research report
- ✅ Citations are clickable and show source details
- ✅ Comparison table displays 2-5 companies side-by-side
- ✅ Time Travel shows historical analysis with trends
- ✅ Knowledge graph renders interactively
- ✅ Valuation calculator updates in real-time

---

### Phase 8: Testing & Documentation (3-4 days)

**Core Objectives**:
1. Unit tests for all agents and RAG components
2. Integration tests for API endpoints
3. End-to-end tests for full workflow
4. API documentation
5. User guide

**Files to Create**:
- `tests/test_agents.py` - Agent unit tests
- `tests/test_rag.py` - RAG pipeline tests
- `tests/test_citations.py` - Citation system tests (NEW)
- `tests/test_comparison.py` - Comparison API tests (NEW)
- `tests/test_api.py` - API integration tests
- `tests/e2e/test_workflow.py` - End-to-end tests
- `docs/API.md` - API documentation
- `docs/USER_GUIDE.md` - User guide

**Validation Criteria**:
- ✅ 80%+ test coverage
- ✅ All API endpoints have integration tests
- ✅ E2E test covers full research generation flow
- ✅ API documentation is complete
- ✅ User guide covers all 5 key features

---

## 🏗️ Technical Architecture (Updated)

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ query / streaming / citations
       ↓
┌─────────────────────────────────────────────────┐
│              FastAPI Backend                     │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │         API Routes                       │  │
│  │  /research  /citations  /compare         │  │
│  │  /history   /graph      /valuation       │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│  ┌──────────────▼───────────────────────────┐  │
│  │      Agent Orchestrator (LangGraph)      │  │
│  │                                           │  │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐     │  │
│  │  │ Market │ │ Fund.  │ │Sentiment │     │  │
│  │  │  Data  │ │Analysis│ │ Analysis │     │  │
│  │  └────────┘ └───┬────┘ └──────────┘     │  │
│  │                 │                         │  │
│  │       ┌─────────▼──────────┐             │  │
│  │       │  Valuation Agent   │ (NEW)       │  │
│  │       └─────────┬──────────┘             │  │
│  │                 │                         │  │
│  │       ┌─────────▼──────────┐             │  │
│  │       │ Competitive Agent  │ (NEW)       │  │
│  │       └─────────┬──────────┘             │  │
│  │                 │                         │  │
│  │       ┌─────────▼──────────┐             │  │
│  │       │   Report Generator │             │  │
│  │       └────────────────────┘             │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│  ┌──────────────▼───────────────────────────┐  │
│  │         RAG Pipeline                     │  │
│  │  ┌──────────┐  ┌────────────────────┐   │  │
│  │  │  SEC     │  │  Hybrid Search     │   │  │
│  │  │  Parser  │→ │  (Vector+Metadata) │   │  │
│  │  └──────────┘  └────────┬───────────┘   │  │
│  │                          │               │  │
│  │                ┌─────────▼──────────┐    │  │
│  │                │ Citation Extractor │    │  │
│  │                └────────────────────┘    │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│  ┌──────────────▼───────────────────────────┐  │
│  │         MongoDB Atlas                    │  │
│  │  ┌────────────┐ ┌──────────────────┐    │  │
│  │  │Conversation│ │  Entity Graph    │    │  │
│  │  │  Memory    │ │ (Knowledge Graph)│    │  │
│  │  └────────────┘ └──────────────────┘    │  │
│  │                                           │  │
│  │  ┌────────────┐ ┌──────────────────┐    │  │
│  │  │ Citations  │ │ Vector Documents │    │  │
│  │  │   Store    │ │  (with metadata) │    │  │
│  │  └────────────┘ └──────────────────┘    │  │
│  │                                           │  │
│  │  ┌──────────────────────────────────┐    │  │
│  │  │   Historical Analysis Store      │    │  │
│  │  │   (Time Travel Support)          │    │  │
│  │  └──────────────────────────────────┘    │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  External Services:                             │
│  ├─ Groq API (LLM)                              │
│  ├─ OpenAI API (Embeddings)                     │
│  ├─ Yahoo Finance API                           │
│  ├─ SEC EDGAR                                   │
│  └─ News APIs                                   │
└──────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────┐
│           React Frontend                         │
│  ┌────────────┐  ┌──────────────────────┐       │
│  │  Research  │  │  Citation Viewer     │ (NEW) │
│  │   Report   │  │  (Modal with source) │       │
│  └────────────┘  └──────────────────────┘       │
│                                                   │
│  ┌────────────┐  ┌──────────────────────┐       │
│  │ Comparison │  │  Time Travel         │ (NEW) │
│  │   Table    │  │  (Historical view)   │       │
│  └────────────┘  └──────────────────────┘       │
│                                                   │
│  ┌─────────────┐ ┌──────────────────────┐       │
│  │  Knowledge  │ │  Valuation           │ (NEW) │
│  │    Graph    │ │  Calculator          │       │
│  └─────────────┘ └──────────────────────┘       │
└───────────────────────────────────────────────────┘
```

---

## 💡 Sample User Interaction Flow

**Scenario**: User wants deep research on Apple

```
1. User Input:
   "Generate a comprehensive investment analysis for AAPL"

2. System Processing (WebSocket streaming):

   [10%] 📊 Market Data Agent working...
          ✓ Current price: $175.30
          ✓ 5-year price history retrieved
          ✓ P/E ratio: 28.5x

   [25%] 📄 Fundamentals Agent analyzing SEC filings...
          ✓ Downloaded 10-K 2020-2024
          ✓ Extracted revenue growth: 3.2% [cite_001]
          ✓ Identified risk factors: 5 key risks [cite_002-006]

   [40%] 📰 Sentiment Agent scanning news...
          ✓ Analyzed 158 articles (last 30 days)
          ✓ Sentiment: 68% positive
          ✓ Key event: Vision Pro launch [Feb 2]

   [60%] 💰 Valuation Agent calculating...
          ✓ DCF target: $192
          ✓ Comps target: $178
          ✓ Average target: $185 (+5.7% upside)

   [80%] 🏢 Competitive Agent comparing...
          ✓ Compared vs MSFT, GOOGL, META
          ✓ Ranked #2 in margins
          ✓ Ranked #4 in growth

   [100%] 📝 Report Generator synthesizing...
           ✓ Report complete!

3. User sees interactive report:

   ═══════════════════════════════════════════════
   APPLE INC. (AAPL) - INVESTMENT RESEARCH REPORT
   Generated: Oct 22, 2024 | Rating: HOLD
   ═══════════════════════════════════════════════

   EXECUTIVE SUMMARY
   • Recommendation: Hold
   • Target Price: $185 (+5.7% upside)
   • Key Thesis: Strong ecosystem and brand, but
     growth slowing. Services business offsetting
     iPhone saturation.

   ───────────────────────────────────────────────

   FINANCIAL PERFORMANCE
   • Revenue: $383B (+3.2% YoY) [¹] 👈 CLICKABLE
   • Net Income: $97B (+2.8% YoY) [²]
   • FCF: $99B [³]
   • Services Revenue: $85B (+16% YoY) [⁴]

   [User clicks [¹]]

   ┌────────────────────────────────────────────┐
   │ Citation Details                           │
   ├────────────────────────────────────────────┤
   │ Source: SEC 10-K 2023                      │
   │ Filed: February 15, 2024                   │
   │ Page: 23                                   │
   │ Section: MD&A - Revenue Analysis           │
   │                                            │
   │ Original Text:                             │
   │ "Net sales increased 3.2% or $11.9 billion │
   │  during 2023 compared to 2022. The increase│
   │  was driven primarily by higher Services   │
   │  revenue..."                               │
   │                                            │
   │ [View Full 10-K] [Add to Research Notes]   │
   └────────────────────────────────────────────┘

   ───────────────────────────────────────────────

   VALUATION ANALYSIS
   • Current Price: $175.30
   • DCF Target: $192 [View Assumptions]
   • Comps Target: $178 [View Peer Comparison]
   • Average Target: $185

   [User clicks "View Peer Comparison"]

   ┌─────────────┬──────┬──────┬──────┬──────┐
   │   Metric    │ AAPL │ MSFT │GOOGL │ META │
   ├─────────────┼──────┼──────┼──────┼──────┤
   │ Rev Growth  │ 3.2% │ 7.8% │ 9.1% │ 11%  │
   │ Net Margin  │ 25.3%│ 36.7%│ 23.1%│ 29%  │✅
   │ P/E Ratio   │ 28.5x│ 32.1x│ 24.2x│ 27x  │
   │ AI Rating   │ Hold │ Buy  │ Buy  │ Buy  │
   └─────────────┴──────┴──────┴──────┴──────┘

   ───────────────────────────────────────────────

   RISKS
   1. iPhone Revenue Dependency (52% of total) [⁵]
   2. China Market Exposure (30% of revenue) [⁶]
   3. Regulatory Scrutiny (App Store model) [⁷]

   ───────────────────────────────────────────────

   [User clicks "Time Travel" button]

   Timeline View:

   2024-04-21: Buy @ $180
   ├─ Revenue growth: 7.8%
   └─ iPhone 15 strong demand

   2024-07-15: Hold @ $182
   ├─ Revenue growth: 5.1%
   └─ Growth moderating

   2024-10-22: Hold @ $185 (Current)
   ├─ Revenue growth: 3.2%
   └─ Services offsetting iPhone weakness

   📊 Trend: Rating downgraded from Buy to Hold
       due to slowing growth

   ───────────────────────────────────────────────

   [User adjusts Valuation Calculator]

   Interactive DCF Model:
   Revenue Growth: [━━●━━━━] 5.0% (adjusted from 3.2%)
   Net Margin:     [━━━●━━━] 25.3%
   WACC:           [━━●━━━━] 8.5%

   → New Target: $198 (vs $192 base case)

   ═══════════════════════════════════════════════

   [Save Report] [Export PDF] [Add to Portfolio]
   [Subscribe to AAPL Updates]

```

---

## 📅 Development Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Setup | ✅ Complete | - |
| Phase 2: MongoDB + Citations | 3-4 days | Week 1 |
| Phase 3: Deep RAG | 4-5 days | Week 1-2 |
| Phase 4: Multi-Agent | 5-6 days | Week 2-3 |
| Phase 5: FastAPI + APIs | 3-4 days | Week 3 |
| Phase 6: Groq Integration | 2-3 days | Week 3-4 |
| Phase 7: Frontend Dashboard | 5-7 days | Week 4-5 |
| Phase 8: Testing + Docs | 3-4 days | Week 5-6 |

**Total Estimated Time**: 5-6 weeks (working part-time)

---

## 🎯 Success Metrics

**Technical Metrics**:
- ✅ Every AI claim has a clickable citation
- ✅ Hybrid search retrieval accuracy > 80%
- ✅ Report generation time < 3 minutes
- ✅ WebSocket streaming latency < 500ms
- ✅ Test coverage > 80%

**User Experience Metrics**:
- ✅ User can verify any claim in < 2 clicks
- ✅ Comparison view supports 2-5 companies
- ✅ Time Travel shows analysis history up to 1 year
- ✅ Knowledge graph renders in < 5 seconds
- ✅ Valuation calculator updates in real-time

**Business Differentiation**:
- ✅ 100% of claims are traceable (vs ValueCell: 0%)
- ✅ Historical analysis comparison (vs ValueCell: none)
- ✅ Deep SEC document parsing (vs ValueCell: basic)
- ✅ Interactive valuation tools (vs ValueCell: none)
- ✅ Knowledge graph visualization (vs ValueCell: none)

---

## 🚀 Post-MVP Roadmap

**Phase 9: Advanced Features** (Future)
- Backtesting framework (test historical recommendations)
- Custom screening (user-defined financial metrics)
- Email/Slack alerts on significant events
- Multi-language support (Chinese for A-share analysis)
- Earnings call transcript analysis
- Insider trading pattern detection

**Phase 10: Platform Expansion** (Future)
- Agent plugin system (community-contributed agents)
- Agent marketplace
- SDK for custom agent development
- White-label offering for institutions

---

## 📌 Key Takeaways

**Our Competitive Advantage vs ValueCell**:

1. **Traceability**: Every claim links to source documents
2. **Depth**: 10-K parsed by section, not just chunked
3. **Learning**: Users understand WHY, not just WHAT
4. **Time Travel**: Historical analysis comparison
5. **Knowledge Graph**: Understand company relationships

**Our Target Users vs ValueCell**:

| Our Users | ValueCell Users |
|-----------|-----------------|
| Value investors (hold 1+ year) | Day traders (hold hours/days) |
| Analysts (need citations) | Retail traders (need speed) |
| Students (learning finance) | Active traders (quick decisions) |
| Institutions (compliance) | Individual investors |

**Our Moat**:

Not multi-market coverage (ValueCell wins), but:
- ✅ **Deepest SEC analysis** in the market
- ✅ **Only platform** with full citation tracking
- ✅ **Only platform** with historical analysis comparison
- ✅ **Only platform** with interactive knowledge graphs
- ✅ **Only platform** teaching users HOW to analyze

---

**Questions before we begin Phase 2?**

This plan is flexible and can be adjusted based on your priorities and time constraints.