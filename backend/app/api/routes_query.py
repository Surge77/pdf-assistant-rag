from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.models.schemas import QueryRequest, QueryResponse, SourceChunk
from app.services.document_store import DocumentStore
from app.services.embed_service import EmbedService
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStore

router = APIRouter(tags=["query"])


@lru_cache
def get_embed_service() -> EmbedService:
    settings = get_settings()
    return EmbedService(model_name=settings.embedding_model)


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(persist_directory=Path(settings.chroma_dir))


@lru_cache
def get_document_store() -> DocumentStore:
    settings = get_settings()
    return DocumentStore(persist_directory=Path(settings.documents_dir))


@lru_cache
def get_llm_service() -> LLMService:
    settings = get_settings()
    return LLMService(base_url=settings.ollama_base_url, model=settings.ollama_model)


@router.post("/query", response_model=QueryResponse)
def query_document(request: QueryRequest) -> QueryResponse:
    try:
        document = get_document_store().get_document(request.document_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc

    if document["status"] == "processing":
        raise HTTPException(status_code=409, detail="Document is still being indexed.")

    if document["status"] != "ready":
        raise HTTPException(status_code=409, detail="Document is not ready for querying.")

    embed_service = get_embed_service()
    vector_store = get_vector_store()
    llm_service = get_llm_service()

    query_embedding = embed_service.embed_texts([request.question])[0]
    sources = vector_store.query(
        document_id=request.document_id,
        query_embedding=query_embedding,
        top_k=request.top_k,
    )

    if not sources:
        return QueryResponse(
            answer="I could not find relevant context in the uploaded PDF to answer that question.",
            model=get_settings().ollama_model,
            prompt_context_count=0,
            sources=[],
        )

    llm_result = llm_service.answer_question(request.question, sources)

    return QueryResponse(
        answer=llm_result["answer"],
        model=llm_result["model"],
        prompt_context_count=llm_result["prompt_context_count"],
        sources=[SourceChunk(**source) for source in sources],
    )
