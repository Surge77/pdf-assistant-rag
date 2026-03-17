from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]
    models: dict[str, str]


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    status: str
    stored_path: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    stored_path: str
    status: str
    page_count: int = 0
    chunk_count: int = 0


class QueryRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=8)


class SourceChunk(BaseModel):
    text: str
    page_number: int
    chunk_index: int
    score: float


class QueryResponse(BaseModel):
    answer: str
    model: str
    prompt_context_count: int
    sources: list[SourceChunk]
