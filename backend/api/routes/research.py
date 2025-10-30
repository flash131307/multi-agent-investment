"""
Research API endpoints for multi-agent investment research system.
Provides REST API for submitting queries and retrieving conversation history.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
import logging
import uuid

from backend.api.models import (
    ResearchQueryRequest,
    ResearchQueryResponse,
    ConversationHistoryResponse,
    SessionListResponse,
    SessionSummary,
    MessageModel,
    ErrorResponse
)
from backend.agents.graph import run_research_query
from backend.memory.conversation import conversation_memory
from backend.rag.pipeline import rag_pipeline

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/research",
    tags=["research"],
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    }
)


@router.post(
    "/query",
    response_model=ResearchQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Research Query",
    description="Submit an investment research query and receive a comprehensive analysis report. "
                "The system uses a multi-agent workflow to gather market data, sentiment analysis, "
                "analyst consensus, and relevant documents to generate the report.",
    responses={
        200: {
            "description": "Research report generated successfully",
            "model": ResearchQueryResponse
        },
        400: {
            "description": "Invalid request (query too short, etc.)",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error during report generation",
            "model": ErrorResponse
        }
    }
)
async def create_research_query(request: ResearchQueryRequest) -> ResearchQueryResponse:
    """
    Submit a research query and receive an investment analysis report.

    The workflow:
    1. Creates or reuses a session
    2. Routes query through multi-agent system
    3. Fetches market data, sentiment, analyst consensus, and RAG context in parallel
    4. Generates comprehensive investment report
    5. Saves to conversation history
    6. Returns report with metadata

    Args:
        request: ResearchQueryRequest with query and optional session_id

    Returns:
        ResearchQueryResponse with report and metadata

    Raises:
        HTTPException: 400 for invalid request, 500 for processing errors
    """
    try:
        # Use provided session_id or create new one
        session_id = request.session_id or str(uuid.uuid4())

        logger.info(f"Processing research query for session {session_id}: {request.query[:50]}...")

        # Run the multi-agent workflow
        final_state = await run_research_query(
            session_id=session_id,
            user_query=request.query
        )

        # Extract data from final state
        report = final_state.get("report", "")
        tickers = final_state.get("tickers", [])
        market_data = final_state.get("market_data", [])
        sentiment = final_state.get("sentiment_analysis", [])
        analyst_consensus = final_state.get("analyst_consensus", [])
        context = final_state.get("retrieved_context", [])
        visualization_data = final_state.get("visualization_data", [])
        snapshot = final_state.get("snapshot")
        report_metadata = final_state.get("report_metadata")

        # Extract execution tracking
        executed_agents = final_state.get("executed_agents", [])
        agent_errors = final_state.get("agent_errors", {})

        # Extract routing decision
        intent = final_state.get("intent")
        routing_flags = {
            "market_data": final_state.get("should_fetch_market_data", False),
            "sentiment": final_state.get("should_analyze_sentiment", False),
            "context": final_state.get("should_retrieve_context", False)
        }

        # Check if report was generated
        if not report:
            logger.error(f"No report generated for session {session_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate research report"
            )

        # Calculate data availability: data exists AND agent succeeded (no error)
        # market_data agent also populates peer_valuation, so check both
        market_data_available = (
            len(market_data) > 0 and "market_data" not in agent_errors
        )
        sentiment_available = (
            len(sentiment) > 0 and "sentiment" not in agent_errors
        )
        analyst_consensus_available = (
            len(analyst_consensus) > 0 and "forward_looking" not in agent_errors
        )

        # Check deep analysis availability (SEC 10-K data) for the primary ticker
        deep_analysis_available = False
        can_request_deep_analysis = False

        if tickers:
            primary_ticker = tickers[0]  # Use first ticker as primary
            deep_analysis_available = await rag_pipeline.has_deep_analysis_data(primary_ticker)

            # User can request deep analysis if:
            # 1. Query has a ticker
            # 2. Deep analysis not already available
            # 3. Query intent suggests depth (not just price_query)
            can_request_deep_analysis = (
                not deep_analysis_available and
                intent not in ["price_query"]
            )

        # Build response
        response = ResearchQueryResponse(
            session_id=session_id,
            query=request.query,
            report=report,
            tickers=tickers,
            executed_agents=executed_agents,
            agent_errors=agent_errors,
            intent=intent,
            routing_flags=routing_flags,
            market_data_available=market_data_available,
            sentiment_available=sentiment_available,
            analyst_consensus_available=analyst_consensus_available,
            context_retrieved=len(context),
            deep_analysis_available=deep_analysis_available,
            can_request_deep_analysis=can_request_deep_analysis,
            visualization_data=visualization_data or [],
            snapshot=snapshot,
            report_metadata=report_metadata
        )

        logger.info(
            f"Successfully generated report for session {session_id} "
            f"(tickers={tickers}, context_docs={len(context)})"
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error processing research query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process research query: {str(e)}"
        )


@router.post(
    "/deep-analysis/{ticker}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request Deep Analysis",
    description="Request deep analysis (SEC 10-K ingestion) for a ticker. "
                "This triggers background download and processing of SEC filings. "
                "Returns immediately with 202 Accepted status. "
                "Once complete, subsequent queries for this ticker will include deep insights.",
    responses={
        202: {
            "description": "Deep analysis request accepted and processing started",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Deep analysis request accepted for NVDA",
                        "ticker": "NVDA",
                        "status": "processing",
                        "estimated_time_seconds": 60
                    }
                }
            }
        },
        400: {
            "description": "Invalid ticker or deep analysis already available",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def request_deep_analysis(ticker: str):
    """
    Request deep analysis for a ticker (downloads and processes SEC 10-K filing).

    This endpoint triggers background processing:
    1. Downloads latest SEC 10-K filing
    2. Chunks the document
    3. Generates embeddings
    4. Stores in vector database

    The request returns immediately (202 Accepted).
    Future queries for this ticker will include deep insights from the 10-K.

    Args:
        ticker: Stock ticker symbol (e.g., "NVDA", "GOOGL")

    Returns:
        Status message with estimated processing time

    Raises:
        HTTPException: 400 if ticker invalid or data already exists, 500 for errors
    """
    try:
        ticker = ticker.upper()

        logger.info(f"Received deep analysis request for {ticker}")

        # Check if deep analysis already available
        has_data = await rag_pipeline.has_deep_analysis_data(ticker)

        if has_data:
            logger.warning(f"Deep analysis already available for {ticker}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Deep analysis data already available for {ticker}"
            )

        # Trigger background ingestion
        # Note: In production, this should use a task queue (Celery, etc.)
        # For now, we'll use asyncio background task
        import asyncio

        async def background_ingestion():
            """Background task to ingest EDGAR filing."""
            try:
                logger.info(f"🚀 Starting background ingestion for {ticker}")
                count = await rag_pipeline.ingest_edgar_filing(ticker, filing_type="10-K", num_filings=1)
                logger.info(f"✅ Background ingestion complete for {ticker}: {count} chunks")
            except Exception as e:
                logger.error(f"❌ Background ingestion failed for {ticker}: {e}")

        # Start background task
        asyncio.create_task(background_ingestion())

        return {
            "message": f"Deep analysis request accepted for {ticker}",
            "ticker": ticker,
            "status": "processing",
            "estimated_time_seconds": 60,
            "note": "Query this ticker again in ~60 seconds to see deep insights from SEC 10-K filing"
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error processing deep analysis request for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process deep analysis request: {str(e)}"
        )


@router.get(
    "/deep-analysis/{ticker}/status",
    status_code=status.HTTP_200_OK,
    summary="Check Deep Analysis Status",
    description="Check if deep analysis data (SEC 10-K) is available for a ticker. "
                "Use this endpoint to poll for completion after requesting deep analysis.",
    responses={
        200: {
            "description": "Status check successful",
            "content": {
                "application/json": {
                    "example": {
                        "ticker": "NVDA",
                        "available": True
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def check_deep_analysis_status(ticker: str):
    """
    Check if deep analysis data is available for a ticker.

    This is a lightweight endpoint for polling after requesting deep analysis.
    Returns immediately with availability status.

    Args:
        ticker: Stock ticker symbol (e.g., "NVDA", "GOOGL")

    Returns:
        Status object with availability boolean

    Raises:
        HTTPException: 500 for errors
    """
    try:
        ticker = ticker.upper()
        available = await rag_pipeline.has_deep_analysis_data(ticker)

        return {
            "ticker": ticker,
            "available": available
        }

    except Exception as e:
        logger.error(f"Error checking deep analysis status for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check deep analysis status: {str(e)}"
        )


@router.get(
    "/history/{session_id}",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Conversation History",
    description="Retrieve the complete conversation history for a specific session. "
                "Returns all messages (user queries and assistant responses) in chronological order.",
    responses={
        200: {
            "description": "Conversation history retrieved successfully",
            "model": ConversationHistoryResponse
        },
        404: {
            "description": "Session not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def get_conversation_history(session_id: str) -> ConversationHistoryResponse:
    """
    Retrieve conversation history for a specific session.

    Args:
        session_id: Unique session identifier

    Returns:
        ConversationHistoryResponse with all messages

    Raises:
        HTTPException: 404 if session not found, 500 for other errors
    """
    try:
        logger.info(f"Retrieving conversation history for session {session_id}")

        # Get messages from MongoDB
        messages = await conversation_memory.get_conversation(session_id, limit=50)

        # Check if session exists (empty list could mean no messages yet or session doesn't exist)
        # We'll also check session info to distinguish between these cases
        session_info = await conversation_memory.get_session_info(session_id)

        if session_info is None and not messages:
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )

        # Convert to response model
        message_models = [
            MessageModel(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            )
            for msg in messages
        ]

        response = ConversationHistoryResponse(
            session_id=session_id,
            messages=message_models,
            message_count=len(message_models)
        )

        logger.info(f"Retrieved {len(message_models)} messages for session {session_id}")

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List All Sessions",
    description="Retrieve a list of all active conversation sessions with metadata. "
                "Sessions are sorted by most recently updated first. "
                "Sessions automatically expire after 24 hours.",
    responses={
        200: {
            "description": "Session list retrieved successfully",
            "model": SessionListResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def list_sessions() -> SessionListResponse:
    """
    List all active conversation sessions.

    Returns sessions sorted by most recently updated first.
    Includes metadata such as message count, timestamps, and first query preview.

    Returns:
        SessionListResponse with list of sessions

    Raises:
        HTTPException: 500 for internal errors
    """
    try:
        logger.info("Retrieving all active sessions")

        # Get database collection
        collection = await conversation_memory._get_collection()

        # Query all sessions, sorted by updated_at (most recent first)
        cursor = collection.find({}).sort("updated_at", -1)
        session_docs = await cursor.to_list(length=100)  # Limit to 100 sessions

        # Convert to response models
        sessions = []
        for doc in session_docs:
            # Skip documents without session_id (old/invalid data)
            if not doc.get("session_id"):
                logger.warning(f"Skipping session document without session_id: {doc.get('_id')}")
                continue

            # Skip documents without required timestamp fields
            if not doc.get("created_at") or not doc.get("updated_at") or not doc.get("expires_at"):
                logger.warning(f"Skipping session document with missing timestamps: {doc.get('session_id')}")
                continue

            messages = doc.get("messages", [])
            message_count = len(messages)

            # Get first user message as preview
            first_query = None
            if messages:
                for msg in messages:
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        # Truncate to 100 chars
                        first_query = content[:100] + "..." if len(content) > 100 else content
                        break

            try:
                session = SessionSummary(
                    session_id=doc["session_id"],
                    user_id=doc.get("user_id"),
                    message_count=message_count,
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"],
                    expires_at=doc["expires_at"],
                    first_query=first_query
                )
                sessions.append(session)
            except Exception as e:
                logger.warning(f"Failed to create SessionSummary for {doc.get('session_id')}: {e}")
                continue

        response = SessionListResponse(
            sessions=sessions,
            total_count=len(sessions)
        )

        logger.info(f"Retrieved {len(sessions)} active sessions")

        return response

    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


# Health check endpoint specific to research API
@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Research API Health Check",
    description="Check if the research API and its dependencies are healthy",
    tags=["health"]
)
async def health_check():
    """
    Health check for research API.

    Verifies:
    - MongoDB connection
    - ChromaDB availability

    Returns:
        Health status with component details
    """
    from backend.services.database import mongodb
    from backend.services.chroma_client import chroma_client

    try:
        # Check MongoDB
        mongo_healthy = await mongodb.health_check()

        # Check ChromaDB (simple check)
        chroma_healthy = False
        try:
            chroma_client.collection.count()
            chroma_healthy = True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")

        overall_healthy = mongo_healthy and chroma_healthy

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "components": {
                "mongodb": "healthy" if mongo_healthy else "unhealthy",
                "chromadb": "healthy" if chroma_healthy else "unhealthy"
            },
            "service": "research-api"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "research-api"
        }
