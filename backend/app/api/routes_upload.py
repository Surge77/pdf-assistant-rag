from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.models.schemas import DocumentStatusResponse, UploadResponse
from app.services.chunk_service import chunk_pages
from app.services.document_store import DocumentStore
from app.services.embed_service import EmbedService
from app.services.pdf_service import extract_pages_from_pdf_bytes
from app.services.vector_store import VectorStore

router = APIRouter(tags=["upload"])


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


def process_document(document_id: str, stored_path: Path) -> None:
    document_store = get_document_store()
    try:
        file_bytes = stored_path.read_bytes()
        page_texts = extract_pages_from_pdf_bytes(file_bytes)
        chunks = chunk_pages(page_texts)

        if chunks:
            embed_service = get_embed_service()
            embeddings = embed_service.embed_texts([str(chunk["text"]) for chunk in chunks])
            get_vector_store().upsert_chunks(
                document_id=document_id,
                chunks=[
                    {
                        "chunk_id": f"{document_id}-{chunk['chunk_index']}",
                        "text": str(chunk["text"]),
                        "page_number": int(chunk["page_number"]),
                        "chunk_index": int(chunk["chunk_index"]),
                        "embedding": embeddings[index],
                    }
                    for index, chunk in enumerate(chunks)
                ],
            )

        document_store.update_document(
            document_id,
            status="ready",
            page_count=len(page_texts),
            chunk_count=len(chunks),
        )
    except Exception:
        document_store.update_document(document_id, status="failed")
        raise


def schedule_document_processing(background_tasks: BackgroundTasks, document_id: str, stored_path: Path) -> None:
    background_tasks.add_task(process_document, document_id, stored_path)


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_bytes = await file.read()
    document_id = str(uuid4())
    stored_path = upload_dir / f"{document_id}-{file.filename}"
    stored_path.write_bytes(file_bytes)
    get_document_store().create_document(
        document_id=document_id,
        filename=file.filename,
        stored_path=stored_path,
        status="processing",
    )
    schedule_document_processing(background_tasks, document_id, stored_path)

    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        page_count=0,
        chunk_count=0,
        status="processing",
        stored_path=str(stored_path.resolve()),
    )


@router.get("/documents/{document_id}", response_model=DocumentStatusResponse)
def get_document_status(document_id: str) -> DocumentStatusResponse:
    try:
        record = get_document_store().get_document(document_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc

    return DocumentStatusResponse(**record)
