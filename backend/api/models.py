"""
Pydantic models for API request/response validation.
Provides type safety and automatic OpenAPI documentation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============= Research Query Models =============

class ResearchQueryRequest(BaseModel):
    """Request model for submitting a research query."""

    query: str = Field(
        ...,
        description="Research question or query (e.g., 'Analyze Microsoft stock')",
        min_length=3,
        max_length=1000,
        examples=["What is the investment outlook for Apple?"]
    )

    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for conversation continuity. If not provided, a new session will be created.",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )


class ResearchQueryResponse(BaseModel):
    """Response model for research query results."""

    session_id: str = Field(
        ...,
        description="Session identifier for this conversation",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

    query: str = Field(
        ...,
        description="The original query submitted",
        examples=["What is the investment outlook for Apple?"]
    )

    report: str = Field(
        ...,
        description="Generated investment research report"
    )

    tickers: List[str] = Field(
        default_factory=list,
        description="Stock tickers identified in the query",
        examples=[["AAPL", "MSFT"]]
    )

    market_data_available: bool = Field(
        ...,
        description="Whether market data was retrieved"
    )

    sentiment_available: bool = Field(
        ...,
        description="Whether sentiment analysis was performed"
    )

    analyst_consensus_available: bool = Field(
        ...,
        description="Whether analyst consensus data was retrieved"
    )

    context_retrieved: int = Field(
        ...,
        description="Number of RAG context documents retrieved",
        ge=0
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the report was generated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "query": "What is the investment outlook for Apple?",
                "report": "# Investment Analysis: Apple Inc. (AAPL)\n\n## Executive Summary\n...",
                "tickers": ["AAPL"],
                "market_data_available": True,
                "sentiment_available": True,
                "analyst_consensus_available": True,
                "context_retrieved": 5,
                "timestamp": "2025-10-26T12:00:00Z"
            }
        }


# ============= Conversation History Models =============

class MessageModel(BaseModel):
    """Individual message in conversation history."""

    role: str = Field(
        ...,
        description="Message role: 'user' or 'assistant'",
        examples=["user", "assistant"]
    )

    content: str = Field(
        ...,
        description="Message content"
    )

    timestamp: datetime = Field(
        ...,
        description="When the message was created"
    )


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""

    session_id: str = Field(
        ...,
        description="Session identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

    messages: List[MessageModel] = Field(
        default_factory=list,
        description="List of messages in chronological order"
    )

    message_count: int = Field(
        ...,
        description="Total number of messages in the conversation",
        ge=0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is the investment outlook for Apple?",
                        "timestamp": "2025-10-26T12:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "# Investment Analysis: Apple Inc. (AAPL)...",
                        "timestamp": "2025-10-26T12:00:15Z"
                    }
                ],
                "message_count": 2
            }
        }


# ============= Session List Models =============

class SessionSummary(BaseModel):
    """Summary information for a single session."""

    session_id: str = Field(
        ...,
        description="Unique session identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

    user_id: Optional[str] = Field(
        None,
        description="User identifier (if available)"
    )

    message_count: int = Field(
        ...,
        description="Number of messages in the session",
        ge=0
    )

    created_at: datetime = Field(
        ...,
        description="When the session was created"
    )

    updated_at: datetime = Field(
        ...,
        description="When the session was last updated"
    )

    expires_at: datetime = Field(
        ...,
        description="When the session will expire (24h TTL)"
    )

    first_query: Optional[str] = Field(
        None,
        description="First message in the conversation (preview)",
        max_length=100
    )


class SessionListResponse(BaseModel):
    """Response model for listing all sessions."""

    sessions: List[SessionSummary] = Field(
        default_factory=list,
        description="List of all active sessions"
    )

    total_count: int = Field(
        ...,
        description="Total number of sessions",
        ge=0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": None,
                        "message_count": 4,
                        "created_at": "2025-10-26T12:00:00Z",
                        "updated_at": "2025-10-26T12:05:00Z",
                        "expires_at": "2025-10-27T12:00:00Z",
                        "first_query": "What is the investment outlook for Apple?"
                    }
                ],
                "total_count": 1
            }
        }


# ============= Error Response Models =============

class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(
        ...,
        description="Error type",
        examples=["ValidationError", "NotFoundError", "InternalServerError"]
    )

    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Session not found", "Invalid query format"]
    )

    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details (optional)"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "NotFoundError",
                "message": "Session not found",
                "detail": {"session_id": "invalid-id"},
                "timestamp": "2025-10-26T12:00:00Z"
            }
        }
