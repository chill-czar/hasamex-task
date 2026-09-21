"""Main FastAPI application for Hasamex Expert Interview Analysis Platform."""

import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.config import settings
from apps.api.app.routes.interviews import router as interviews_router
from apps.api.app.routes.guide import router as guide_router
from apps.api.app.routes.insights import router as insights_router
from apps.api.app.routes.questions import router as questions_router
from apps.api.app.services.repository import get_repository
from apps.api.app.services.file_search import get_file_search_service
from apps.api.app.services.analyzer import get_analyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hasamex.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm canonical repository and persisted database cache on startup."""
    try:
        repo = get_repository()
        analyzer = get_analyzer()
        analyzer.warm_cache()
        logger.info(f"Startup complete: {len(repo.get_all_calls())} canonical calls indexed, cache ready.")
    except Exception as e:
        logger.warning(f"Error during startup cache warming: {e}")
    yield


app = FastAPI(
    title="Hasamex Expert Interview Analysis Platform API",
    description="Evidence-grounded analysis of European Robotic Surgery expert interview calls.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Tracks request latency and structured observability metadata."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

    if not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi"):
        logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Latency: {duration_ms:.2f}ms")

    return response


# Include feature routers
app.include_router(interviews_router)
app.include_router(guide_router)
app.include_router(insights_router)
app.include_router(questions_router)


@app.get("/api/health")
async def health_check():
    """Health check returning platform status and configuration details."""
    repo = get_repository()
    fs_service = get_file_search_service()

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "gemini_configured": settings.is_gemini_available,
        "file_search_available": fs_service.is_available(),
        "canonical_calls_loaded": len(repo.get_all_calls()),
        "canonical_experts_loaded": len(repo.get_all_experts()),
    }


@app.post("/api/ingestion")
async def run_ingestion():
    """Re-syncs canonical transcripts and indexes into Google File Search Store."""
    repo = get_repository()
    repo.reload()
    fs_service = get_file_search_service()
    fs_result = fs_service.initialize_store_and_index_transcripts()

    return {
        "canonical_status": "success",
        "calls_ingested": len(repo.get_all_calls()),
        "segments_ingested": len(repo.segments_by_id),
        "file_search": fs_result,
    }


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Hasamex Interview Analyst API",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.app.main:app", host="0.0.0.0", port=8000, reload=True)
