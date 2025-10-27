"""
LangGraph workflow definition for multi-agent research system.
Uses LangGraph 1.0+ API with parallel execution support.
"""
import logging
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langgraph.types import Send
from typing import Literal

from backend.agents.state import AgentState, create_initial_state
from backend.agents.router_agent import router_agent
from backend.agents.market_data_agent import market_data_agent
from backend.agents.sentiment_agent import sentiment_agent
from backend.agents.forward_looking_agent import forward_looking_agent
from backend.agents.report_agent import report_agent
from backend.rag.pipeline import rag_pipeline
from backend.memory.conversation import conversation_memory

logger = logging.getLogger(__name__)


# Helper nodes for memory and RAG


async def memory_loader(state: AgentState) -> AgentState:
    """
    Load conversation history from MongoDB.

    Args:
        state: Current state

    Returns:
        State with conversation history loaded
    """
    session_id = state.get("session_id")

    try:
        # Load conversation history (returns empty list if session doesn't exist)
        messages = await conversation_memory.get_conversation(session_id, limit=10)

        logger.info(f"Loaded {len(messages)} historical messages for session {session_id}")

        # Only update if we got messages, otherwise keep existing (empty) history
        if messages:
            return {"conversation_history": messages}
        else:
            return {}  # No updates needed

    except Exception as e:
        logger.warning(f"Failed to load conversation history: {e}")
        return {}  # Return empty dict, no updates


async def rag_retrieval(state: AgentState) -> AgentState:
    """
    Retrieve relevant documents from RAG pipeline.

    Args:
        state: Current state

    Returns:
        State with retrieved_context populated
    """
    query = state.get("user_query", "")
    tickers = state.get("tickers", [])

    if not query:
        logger.warning("No query specified, skipping RAG retrieval")
        return {"retrieved_context": []}

    try:
        # Retrieve context with or without ticker
        # If tickers present, use first one for metadata filtering
        # Otherwise, rely on semantic search across all documents
        ticker = tickers[0] if tickers else None

        if ticker:
            logger.info(f"Retrieving context for ticker: {ticker}")
            results = await rag_pipeline.retrieve_context(
                query=query,
                ticker=ticker,
                top_k=5
            )
        else:
            logger.info("No tickers specified, using semantic search across all documents")
            results = await rag_pipeline.retrieve_context(
                query=query,
                top_k=5
            )

        # Convert to RetrievedContext format
        retrieved = []
        for r in results:
            retrieved.append({
                "text": r.get("text", ""),
                "source": r.get("metadata", {}).get("source", "unknown"),
                "ticker": r.get("metadata", {}).get("ticker", ticker or "N/A"),
                "similarity": r.get("similarity", 0.0),
                "metadata": r.get("metadata", {})
            })

        logger.info(f"Retrieved {len(retrieved)} context documents")

        # Return only the field we're updating (for parallel execution)
        return {"retrieved_context": retrieved}

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return {"retrieved_context": []}  # Return empty list on error


async def memory_saver(state: AgentState) -> AgentState:
    """
    Save final report to conversation history.

    Args:
        state: Current state with report

    Returns:
        Empty dict (no state updates needed)
    """
    session_id = state.get("session_id")
    report = state.get("report")

    if not report:
        logger.warning("No report to save")
        return {}

    try:
        # Save user query
        await conversation_memory.save_message(
            session_id, "user", state.get("user_query", "")
        )

        # Save assistant response
        await conversation_memory.save_message(
            session_id, "assistant", report
        )

        logger.info(f"Saved conversation to session {session_id}")

    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")

    return {}  # No state updates needed


# Router logic for parallel execution


def route_to_agents(state: AgentState) -> list[Send]:
    """
    Dynamic router that sends to multiple agents in parallel.

    Uses LangGraph 1.0+ Send API for parallel execution.
    Each agent should be sent to exactly once to avoid concurrent updates.

    Args:
        state: Current state after router analysis

    Returns:
        List of Send objects for parallel execution
    """
    sends = []
    sent_to = set()  # Track which agents we've already queued

    # Always retrieve context if enabled
    if state.get("should_retrieve_context", True):
        sends.append(Send("rag_retrieval", state))
        sent_to.add("rag_retrieval")

    # Fetch market data if needed and has tickers
    if state.get("should_fetch_market_data", False) and state.get("tickers"):
        if "market_data" not in sent_to:
            sends.append(Send("market_data", state))
            sent_to.add("market_data")

    # Analyze sentiment if needed and has tickers
    if state.get("should_analyze_sentiment", False) and state.get("tickers"):
        if "sentiment" not in sent_to:
            sends.append(Send("sentiment", state))
            sent_to.add("sentiment")

    # Fetch analyst consensus if has tickers (always useful for forward-looking analysis)
    if state.get("tickers"):
        if "forward_looking" not in sent_to:
            sends.append(Send("forward_looking", state))
            sent_to.add("forward_looking")

    # If no specific agents selected, default to market_data + sentiment (but only once each)
    if state.get("tickers") and len(sent_to) <= 2:  # Only RAG + forward_looking or less
        if "market_data" not in sent_to:
            sends.append(Send("market_data", state))
            sent_to.add("market_data")
        if "sentiment" not in sent_to:
            sends.append(Send("sentiment", state))
            sent_to.add("sentiment")

    logger.info(f"Routing to {len(sent_to)} agents in parallel: {sent_to}")

    return sends


def aggregate_results(state: AgentState) -> AgentState:
    """
    Aggregates results from parallel agent execution.

    This node collects all outputs before sending to report generator.

    Args:
        state: State with partial results from parallel agents

    Returns:
        Empty dict (no state updates, just synchronization point)
    """
    logger.info("Aggregating results from parallel agents")

    # Log what we have
    has_market = state.get("market_data") is not None
    has_sentiment = state.get("sentiment_analysis") is not None
    has_context = state.get("retrieved_context") is not None
    has_analyst = state.get("analyst_consensus") is not None

    logger.info(
        f"Results: market_data={has_market}, "
        f"sentiment={has_sentiment}, analyst_consensus={has_analyst}, context={has_context}"
    )

    return {}  # No state updates, just a synchronization point


# Build the graph


def create_research_graph():
    """
    Create the LangGraph workflow for investment research.

    Flow:
        START
          ↓
        memory_loader
          ↓
        router
          ↓
        [parallel: market_data, sentiment, rag_retrieval]
          ↓
        aggregator
          ↓
        report
          ↓
        memory_saver
          ↓
        END

    Returns:
        Compiled StateGraph
    """
    # Create graph with AgentState
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("memory_loader", memory_loader)
    workflow.add_node("router", router_agent)
    workflow.add_node("market_data", market_data_agent)
    workflow.add_node("sentiment", sentiment_agent)
    workflow.add_node("forward_looking", forward_looking_agent)
    workflow.add_node("rag_retrieval", rag_retrieval)
    workflow.add_node("aggregator", aggregate_results)
    workflow.add_node("report", report_agent)
    workflow.add_node("memory_saver", memory_saver)

    # Define edges
    workflow.add_edge(START, "memory_loader")
    workflow.add_edge("memory_loader", "router")

    # Conditional parallel routing
    workflow.add_conditional_edges(
        "router",
        route_to_agents,
        ["market_data", "sentiment", "forward_looking", "rag_retrieval"]
    )

    # All parallel paths converge to aggregator
    workflow.add_edge("market_data", "aggregator")
    workflow.add_edge("sentiment", "aggregator")
    workflow.add_edge("forward_looking", "aggregator")
    workflow.add_edge("rag_retrieval", "aggregator")

    # Linear flow after aggregation
    workflow.add_edge("aggregator", "report")
    workflow.add_edge("report", "memory_saver")
    workflow.add_edge("memory_saver", END)

    # Compile the graph
    return workflow.compile()


# Create singleton instance
research_graph = create_research_graph()


# Convenience function for running the graph


async def run_research_query(
    session_id: str,
    user_query: str
) -> AgentState:
    """
    Run a research query through the complete agent workflow.

    Args:
        session_id: Unique session identifier
        user_query: User's research question

    Returns:
        Final AgentState with report
    """
    logger.info(f"Starting research query: {user_query[:50]}...")

    # Create initial state
    initial_state = create_initial_state(session_id, user_query)

    # Run the graph
    final_state = await research_graph.ainvoke(initial_state)

    logger.info("Research query completed")

    return final_state
