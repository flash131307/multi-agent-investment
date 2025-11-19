"""
Agent state definitions for LangGraph workflow.
Uses TypedDict for type safety and immutable state management.
"""
from typing import TypedDict, List, Optional, Dict, Any, Literal, Annotated
from typing_extensions import TypedDict as ExtTypedDict
from datetime import datetime
import operator


class AgentMessage(TypedDict):
    """Single message in conversation history."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str


class MarketData(TypedDict):
    """Market data from Yahoo Finance."""
    ticker: str
    current_price: Optional[float]
    change_percent: Optional[float]
    volume: Optional[int]
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    day_high: Optional[float]
    day_low: Optional[float]
    year_high: Optional[float]
    year_low: Optional[float]
    # 52-week trend analysis
    week_52_position: Optional[float]  # Current price position in 52-week range (0-100%)
    distance_from_high: Optional[float]  # % below 52-week high
    distance_from_low: Optional[float]  # % above 52-week low
    trend_signal: Optional[str]  # "near_high", "near_low", "mid_range"


class SentimentAnalysis(TypedDict):
    """Sentiment analysis results."""
    ticker: str
    overall_sentiment: Literal["positive", "neutral", "negative"]
    confidence: float  # 0.0 to 1.0
    key_themes: List[str]
    news_count: int
    summary: str


class AnalystConsensus(TypedDict):
    """Analyst consensus and forward-looking guidance."""
    ticker: str
    target_price_mean: Optional[float]  # Average analyst target price
    target_price_high: Optional[float]  # Highest analyst target price
    target_price_low: Optional[float]   # Lowest analyst target price
    current_price: Optional[float]      # Current price for reference
    upside_potential: Optional[float]   # % upside to mean target (can be negative)
    recommendation: Optional[str]       # "strong_buy", "buy", "hold", "sell", "strong_sell"
    num_analysts: Optional[int]         # Number of analysts covering


class PeerValuation(TypedDict):
    """Peer valuation comparison with sector averages."""
    ticker: str
    sector: Optional[str]
    industry: Optional[str]
    # Company's valuation ratios
    pe_ratio: Optional[float]
    price_to_book: Optional[float]
    price_to_sales: Optional[float]
    # Sector/peer averages
    sector_avg_pe: Optional[float]
    sector_avg_pb: Optional[float]
    sector_avg_ps: Optional[float]
    # Relative valuation
    pe_premium_discount: Optional[float]  # % difference from sector avg (positive = premium, negative = discount)
    pb_premium_discount: Optional[float]
    ps_premium_discount: Optional[float]
    # Peer count for context
    peer_count: int


class RetrievedContext(TypedDict):
    """Retrieved document from RAG."""
    text: str
    source: str  # "edgar", "news", "yfinance"
    ticker: str
    similarity: float
    metadata: Dict[str, Any]


class PricePoint(TypedDict):
    """Single price data point for visualization."""
    date: str  # ISO format date
    open: float
    high: float
    low: float
    close: float
    volume: int


class VisualizationData(TypedDict):
    """Structured data for frontend visualization."""
    ticker: str
    # Historical price data (1 year daily)
    price_history: List[PricePoint]
    # 52-week range visualization
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    current_price: Optional[float]
    current_position_pct: Optional[float]  # Position in 52-week range (0-100%)
    # Peer comparison data
    peer_comparison: List[Dict[str, Any]]  # [{ticker, pe_ratio, pb_ratio, ps_ratio}, ...]
    # Summary stats
    period_high: Optional[float]
    period_low: Optional[float]
    average_volume: Optional[int]


class InvestorSnapshot(TypedDict):
    """Simplified snapshot for beginner investors."""
    ticker: str
    # Core metrics
    current_price: Optional[float]
    price_change_pct: Optional[float]
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    # AI-generated investment recommendation
    investment_rating: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
    rating_explanation: str  # Short explanation (1-2 sentences)
    # Key highlights (3-5 points)
    key_highlights: List[str]  # ["Highlight 1", "Highlight 2", ...]
    # Risk warnings (2-3 points)
    risk_warnings: List[str]  # ["Risk 1", "Risk 2", ...]


class ReportMetadata(TypedDict):
    """Metadata about report generation and agent execution."""
    executed_agents: List[str]  # Which agents ran
    data_sources: Dict[str, bool]  # Which data sources have data
    intent: str  # Query intent
    tickers: List[str]  # Tickers analyzed
    report_template: str  # Which template was used


class AgentState(TypedDict):
    """
    Complete state for multi-agent workflow.

    LangGraph passes this state through all nodes.
    Fields without Annotated are last-write-wins.
    Fields with Annotated[..., operator.add] merge values from parallel nodes.
    """
    # Session info (immutable, set once)
    session_id: str
    user_query: str
    conversation_history: List[AgentMessage]

    # Router output (set by router only)
    intent: Literal[
        "price_query",         # Current price/market data
        "fundamental_analysis", # Financial metrics, ratios
        "sentiment_analysis",   # News and sentiment
        "general_research",     # Comprehensive report
        "comparison"            # Compare multiple stocks
    ]
    tickers: List[str]  # Extracted tickers (e.g., ["AAPL", "MSFT"])

    # Agent execution flags (for routing logic)
    should_fetch_market_data: bool
    should_analyze_sentiment: bool
    should_retrieve_context: bool

    # Execution tracking
    executed_agents: Annotated[List[str], operator.add]  # Track which agents ran
    agent_errors: Annotated[Dict[str, str], operator.or_]  # Track agent-specific errors {agent_name: error_message}
    agent_metrics: Annotated[Dict[str, Dict[str, Any]], operator.or_]  # Agent performance metrics {agent_name: {execution_time, tokens, etc.}}
    reasoning_chains: Annotated[Dict[str, List[str]], operator.or_]  # Agent reasoning steps {agent_name: [step1, step2, ...]}

    # Agent outputs (can be set by parallel agents - use Annotated to merge lists)
    market_data: Annotated[List[MarketData], operator.add]
    sentiment_analysis: Annotated[List[SentimentAnalysis], operator.add]
    retrieved_context: Annotated[List[RetrievedContext], operator.add]
    analyst_consensus: Annotated[List[AnalystConsensus], operator.add]
    peer_valuation: Annotated[List[PeerValuation], operator.add]
    visualization_data: Annotated[List[VisualizationData], operator.add]

    # Final output
    report: Optional[str]
    snapshot: Optional[InvestorSnapshot]  # Simplified snapshot for beginners
    report_metadata: Optional[ReportMetadata]  # Report generation metadata

    # Error handling (use Annotated to merge errors from multiple agents)
    errors: Annotated[List[str], operator.add]

    # Metadata
    timestamp: str
    total_tokens_used: int
    retry_count: int


def create_initial_state(
    session_id: str,
    user_query: str,
    conversation_history: Optional[List[AgentMessage]] = None
) -> AgentState:
    """
    Create initial agent state for a new query.

    Args:
        session_id: Unique session identifier
        user_query: User's research query
        conversation_history: Previous messages (optional)

    Returns:
        Initial AgentState
    """
    return AgentState(
        session_id=session_id,
        user_query=user_query,
        conversation_history=conversation_history or [],

        # Will be set by router
        intent="general_research",
        tickers=[],

        # Routing flags
        should_fetch_market_data=False,
        should_analyze_sentiment=False,
        should_retrieve_context=False,

        # Execution tracking
        executed_agents=[],
        agent_errors={},
        agent_metrics={},
        reasoning_chains={},

        # Agent outputs (initially empty lists for parallel merge)
        market_data=[],
        sentiment_analysis=[],
        retrieved_context=[],
        analyst_consensus=[],
        peer_valuation=[],
        visualization_data=[],

        # Final output
        report=None,
        snapshot=None,
        report_metadata=None,

        # Error handling
        errors=[],
        retry_count=0,

        # Metadata
        timestamp=datetime.utcnow().isoformat(),
        total_tokens_used=0
    )
