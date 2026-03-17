from fastapi.testclient import TestClient

import app.api.routes_query as routes_query
from app.main import create_app
from app.services.document_store import DocumentStore
from app.services.vector_store import VectorStore


class FakeEmbedService:
    def embed_texts(self, texts):
        return [[1.0, 0.0] for _ in texts]


class FakeLLMService:
    def __init__(self):
        self.calls = []

    def answer_question(self, question, chunks):
        self.calls.append({"question": question, "chunks": chunks})
        return {
            "answer": "Paris is the capital of France.",
            "model": "mistral:latest",
            "prompt_context_count": len(chunks),
        }


def test_query_endpoint_requires_non_empty_question():
    client = TestClient(create_app())

    response = client.post(
        "/api/query",
        json={"document_id": "doc-1", "question": ""},
    )

    assert response.status_code == 422


def test_query_endpoint_returns_grounded_answer(tmp_path, monkeypatch):
    chroma_dir = tmp_path / "chroma"
    document_dir = tmp_path / "documents"
    fake_llm = FakeLLMService()

    vector_store = VectorStore(persist_directory=chroma_dir)
    document_store = DocumentStore(persist_directory=document_dir)
    document_store.create_document(
        document_id="doc-1",
        filename="doc.pdf",
        stored_path=tmp_path / "doc.pdf",
        status="ready",
        page_count=1,
        chunk_count=1,
    )
    vector_store.upsert_chunks(
        document_id="doc-1",
        chunks=[
            {
                "chunk_id": "doc-1-0",
                "text": "Paris is the capital of France.",
                "page_number": 2,
                "chunk_index": 0,
                "embedding": [1.0, 0.0],
            }
        ],
    )

    monkeypatch.setattr(routes_query, "get_embed_service", lambda: FakeEmbedService())
    monkeypatch.setattr(routes_query, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(routes_query, "get_vector_store", lambda: vector_store)
    monkeypatch.setattr(routes_query, "get_document_store", lambda: document_store)

    client = TestClient(create_app())
    response = client.post(
        "/api/query",
        json={"document_id": "doc-1", "question": "What is the capital of France?", "top_k": 3},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["answer"] == "Paris is the capital of France."
    assert payload["model"] == "mistral:latest"
    assert payload["sources"][0]["page_number"] == 2
    assert payload["sources"][0]["text"] == "Paris is the capital of France."
    assert fake_llm.calls[0]["question"] == "What is the capital of France?"


def test_query_endpoint_handles_missing_context(tmp_path, monkeypatch):
    vector_store = VectorStore(persist_directory=tmp_path / "chroma")
    document_store = DocumentStore(persist_directory=tmp_path / "documents")
    document_store.create_document(
        document_id="missing-doc",
        filename="missing.pdf",
        stored_path=tmp_path / "missing.pdf",
        status="ready",
        page_count=1,
        chunk_count=0,
    )
    fake_llm = FakeLLMService()

    monkeypatch.setattr(routes_query, "get_embed_service", lambda: FakeEmbedService())
    monkeypatch.setattr(routes_query, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(routes_query, "get_vector_store", lambda: vector_store)
    monkeypatch.setattr(routes_query, "get_document_store", lambda: document_store)

    client = TestClient(create_app())
    response = client.post(
        "/api/query",
        json={"document_id": "missing-doc", "question": "What is this document about?"},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["answer"] == "I could not find relevant context in the uploaded PDF to answer that question."
    assert payload["sources"] == []
    assert fake_llm.calls == []


def test_query_endpoint_rejects_document_that_is_still_processing(tmp_path, monkeypatch):
    document_store = DocumentStore(persist_directory=tmp_path / "documents")
    document_store.create_document(
        document_id="doc-processing",
        filename="processing.pdf",
        stored_path=tmp_path / "processing.pdf",
        status="processing",
    )

    monkeypatch.setattr(routes_query, "get_document_store", lambda: document_store)

    client = TestClient(create_app())
    response = client.post(
        "/api/query",
        json={"document_id": "doc-processing", "question": "What is this document about?"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Document is still being indexed."
