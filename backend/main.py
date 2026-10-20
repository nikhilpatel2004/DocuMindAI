"""FastAPI application factory for DocuMind AI."""
from __future__ import annotations

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import AppError
from app.models.database import init_db

setup_logging()
log = get_logger(__name__)

# Ensure the database tables and indexes exist on startup.
init_db()

app = fastapi.FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="DocuMind AI — private document Q&A with local models",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    # Keep the spec under /api so the Vite dev proxy forwards it instead of
    # returning the SPA index.html (Swagger UI needs JSON here).
    openapi_url="/api/v1/openapi.json",
)

# CORS — configured from env; default allows local dev origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
from app.api.routes import router
from app.api.chat import router as chat_router

app.include_router(router)
app.include_router(chat_router)


@app.get("/openapi.json", include_in_schema=False)
async def legacy_openapi_redirect():
    """Keep the previous spec path working for existing tools."""
    return RedirectResponse(url="/api/v1/openapi.json")


@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    """Map application errors to their declared HTTP status codes."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    """Catch-all so clients always get a JSON error instead of a bare 500."""
    import logging
    logging.getLogger("app").exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )

# Health check
@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": settings.app_name}


@app.get("/", include_in_schema=False)
async def root():
    """Landing response so the API host does not look broken when opened directly."""
    return {
        "service": settings.app_name,
        "status": "ok",
        "message": "DocuMind AI API is running. Open the web UI at http://localhost:5173.",
        "docs": "/api/v1/docs",
        "health": "/healthz",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return an empty response instead of a noisy 404 in the browser console."""
    return Response(status_code=204)


@app.on_event("startup")
async def _preload_embedding_model():
    """Warm up the Sentence Transformers embedding model in the background.

    The first upload/chat would otherwise trigger a multi-second download +
    load that can exceed proxy timeouts. Preloading removes that spike.
    """
    import threading

    def _load():
        try:
            from app.services.rag import get_embedding_model
            get_embedding_model()
            log.info("Embedding model preloaded")
        except Exception as exc:
            log.warning("Embedding model preload failed (will retry on first use): %s", exc)

    threading.Thread(target=_load, daemon=True).start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
