"""
FastAPI application entry point — Multi-Agent Investment Research System.
Decision Hub architecture: 3 agents → signal fusion → BUY/NEUTRAL/SELL.
"""
import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import research

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Agent Investment Research System",
    description=(
        "Equity signal fusion platform using 3 parallel analysis agents "
        "(Technical ReAct, FinBERT Sentiment, Plan-and-Solve Fundamental) "
        "fused by a mathematical Decision Hub."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Multi-Agent Investment Research System v2.0")
    logger.info("Architecture: 3 Agents + Decision Hub")
    logger.info("=" * 60)

    # Optional: pre-warm FinBERT (lazy-loaded by default)
    try:
        from backend.config.settings import settings
        if settings.environment != "development":
            from backend.services.finbert_service import get_finbert_service
            svc = get_finbert_service()
            if svc.is_available():
                logger.info("FinBERT pre-warm skipped (lazy load enabled)")
    except Exception as exc:
        logger.warning("Startup check warning: %s", exc)

    # Optional: Qdrant health check
    try:
        from backend.config.settings import settings
        if settings.qdrant_url != ":memory:":
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{settings.qdrant_url}/healthz")
                if resp.status_code == 200:
                    logger.info("Qdrant healthy at %s", settings.qdrant_url)
                else:
                    logger.warning("Qdrant returned %d", resp.status_code)
    except Exception as exc:
        logger.warning("Qdrant health check skipped: %s", exc)

    logger.info("API docs available at /docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Multi-Agent Investment Research System")


app.include_router(research.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Multi-Agent Investment Research System",
        "version": "2.0.0",
        "status": "running",
        "architecture": "3 Agents + Decision Hub",
        "endpoints": {
            "docs": "/docs",
            "analyze": "POST /api/research/analyze",
            "health": "GET /health",
            "research_health": "GET /api/research/health",
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "investment-research-api",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    from backend.config.settings import settings

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )
