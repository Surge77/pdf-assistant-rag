from pathlib import Path

import httpx
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_query import router as query_router
from app.api.routes_upload import router as upload_router
from app.core.config import get_settings
from app.models.schemas import HealthResponse


def _ollama_status(base_url: str) -> str:
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=1.5)
        return "ready" if response.is_success else "unreachable"
    except httpx.HTTPError:
        return "unreachable"


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(upload_router, prefix=settings.api_prefix)
    app.include_router(query_router, prefix=settings.api_prefix)

    @app.get(f"{settings.api_prefix}/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        vector_store_status = "ready" if Path(settings.chroma_dir).exists() else "missing"

        return HealthResponse(
            status="ok",
            services={
                "vector_store": vector_store_status,
                "ollama": _ollama_status(settings.ollama_base_url),
            },
            models={
                "llm": settings.ollama_model,
                "embedding": settings.embedding_model,
            },
        )

    return app


app = create_app()
