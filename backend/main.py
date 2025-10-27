"""
FastAPI application entry point for Multi-Agent Investment Research System.
Phase 5: REST API endpoints with multi-agent research workflow.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

# Import routers
from backend.api.routes import research

# Import database services
from backend.services.database import mongodb
from backend.memory.conversation import conversation_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Multi-Agent Investment Research System",
    description=(
        "Automated equity research platform using LangGraph multi-agent orchestration. "
        "Features include real-time market data, sentiment analysis, analyst consensus, "
        "SEC EDGAR filings retrieval, and comprehensive investment reports."
    ),
    version="0.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Investment Research API",
        "url": "https://github.com/yourusername/investment-research"
    },
    license_info={
        "name": "MIT"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("=" * 60)
    logger.info("Starting Multi-Agent Investment Research System")
    logger.info("Phase 5: REST API with Multi-Agent Workflow")
    logger.info("=" * 60)

    try:
        # Connect to MongoDB
        await mongodb.connect()
        logger.info("✅ MongoDB connected")

        # Create conversation indexes
        await conversation_memory.create_indexes()
        logger.info("✅ MongoDB indexes created")

        logger.info("=" * 60)
        logger.info("🚀 System ready! API docs available at /docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("=" * 60)
    logger.info("Shutting down Multi-Agent Investment Research System")
    logger.info("=" * 60)

    try:
        # Close MongoDB connection
        await mongodb.close()
        logger.info("✅ MongoDB connection closed")

        logger.info("👋 Shutdown complete")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# Include routers
app.include_router(research.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Multi-Agent Investment Research System",
        "version": "0.5.0",
        "status": "running",
        "phase": "Phase 5: REST API with Multi-Agent Workflow",
        "features": [
            "Multi-agent LangGraph orchestration",
            "Real-time market data (Yahoo Finance)",
            "Sentiment analysis (news + social)",
            "Analyst consensus & price targets",
            "SEC EDGAR filings retrieval",
            "52-week trend analysis",
            "Peer valuation comparison"
        ],
        "endpoints": {
            "docs": "/docs",
            "research_query": "POST /api/research/query",
            "conversation_history": "GET /api/research/history/{session_id}",
            "list_sessions": "GET /api/research/sessions",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Checks connectivity to MongoDB and returns system status.
    """
    try:
        # Check MongoDB health
        mongo_healthy = await mongodb.health_check()

        return {
            "status": "healthy" if mongo_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "investment-research-api",
            "phase": "5",
            "components": {
                "mongodb": "healthy" if mongo_healthy else "unhealthy",
                "api": "healthy"
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "investment-research-api",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
