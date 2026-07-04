from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.db import Base, engine, ensure_schema
from app.routers import candidates, stock, analyze, scan, news, economic, watchlist, outcomes, briefing, alerts, ticker_tape, charts, movers, news_analyze, settings as settings_router
from app.collectors.universe import seed_default_watchlist
from app import runtime_config
from app.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create tables and apply lightweight migrations
Base.metadata.create_all(bind=engine)
ensure_schema()
seed_default_watchlist()
runtime_config.load()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events: startup and shutdown
    """
    # Startup
    logger.info("Starting Pre-Market Dashboard API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down")
    stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(candidates.router, prefix="/api", tags=["candidates"])
app.include_router(stock.router, prefix="/api", tags=["stock"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(scan.router, prefix="/api", tags=["scan"])
app.include_router(news.router, prefix="/api", tags=["news"])
app.include_router(economic.router, prefix="/api", tags=["economic"])
app.include_router(watchlist.router, prefix="/api", tags=["watchlist"])
app.include_router(outcomes.router, prefix="/api", tags=["outcomes"])
app.include_router(briefing.router, prefix="/api", tags=["briefing"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(ticker_tape.router, prefix="/api", tags=["ticker-tape"])
app.include_router(charts.router, prefix="/api", tags=["charts"])
app.include_router(movers.router, prefix="/api", tags=["movers"])
app.include_router(news_analyze.router, prefix="/api", tags=["news-analyze"])
app.include_router(settings_router.router, prefix="/api", tags=["settings"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
