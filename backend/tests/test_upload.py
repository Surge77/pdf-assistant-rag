from pathlib import Path

from fastapi.testclient import TestClient

import app.api.routes_upload as routes_upload
from app.core.config import get_settings
from app.main import create_app
from app.services.document_store import DocumentStore
from app.services.chunk_service import chunk_pages, chunk_text, normalize_text
from app.services.vector_store import VectorStore


def _build_pdf_bytes(texts: str | list[str]) -> bytes:
    page_texts = [texts] if isinstance(texts, str) else texts

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Count {len(page_texts)} /Kids "
        f"[{' '.join(f'{3 + (index * 2)} 0 R' for index in range(len(page_texts)))}] >>".encode("utf-8"),
    ]

    for index, text in enumerate(page_texts):
        page_object_id = 3 + (index * 2)
        content_object_id = page_object_id + 1
        safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content = f"BT\n/F1 12 Tf\n72 720 Td\n({safe_text}) Tj\nET".encode("utf-8")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {3 + (len(page_texts) * 2)} 0 R >> >> "
            f"/Contents {content_object_id} 0 R >>".encode("utf-8")
        )
        objects.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content))

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    parts = [b"%PDF-1.4\n"]
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in parts))
        parts.append(f"{index} 0 obj\n".encode("utf-8"))
        parts.append(obj)
        parts.append(b"\nendobj\n")

    xref_start = sum(len(part) for part in parts)
    parts.append(f"xref\n0 {len(objects) + 1}\n".encode("utf-8"))
    parts.append(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        parts.append(f"{offset:010d} 00000 n \n".encode("utf-8"))

    parts.append(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("utf-8")
    )

    return b"".join(parts)


def test_normalize_text_replaces_common_pdf_ligatures():
    assert normalize_text("public ﬁlings and ﬂows with ﬀ symbols") == "public filings and flows with ff symbols"


def test_chunk_text_creates_overlap_for_long_text():
    text = "alpha beta gamma delta epsilon zeta eta theta"

    chunks = chunk_text(text, chunk_size=20, chunk_overlap=8)

    assert len(chunks) >= 3
    assert chunks[0] == "alpha beta gamma"
    assert chunks[1].startswith("gamma ")
    assert all(chunk == normalize_text(chunk) for chunk in chunks)
    assert all(not chunk.startswith(" ") and not chunk.endswith(" ") for chunk in chunks)


def test_chunk_pages_preserves_real_page_numbers():
    chunks = chunk_pages(
        ["alpha beta gamma delta epsilon", "page two carries the answer"],
        chunk_size=20,
        chunk_overlap=8,
    )

    assert chunks[0]["page_number"] == 1
    assert any(chunk["page_number"] == 2 for chunk in chunks)
    assert any("page two" in str(chunk["text"]) for chunk in chunks if chunk["page_number"] == 2)


def test_upload_endpoint_extracts_pdf_and_saves_file(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    upload_dir = data_dir / "uploads"
    chroma_dir = data_dir / "chroma"

    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("CHROMA_DIR", str(chroma_dir))
    monkeypatch.setenv("DOCUMENTS_DIR", str(data_dir / "documents"))
    get_settings.cache_clear()
    routes_upload.get_embed_service.cache_clear()
    routes_upload.get_vector_store.cache_clear()
    routes_upload.get_document_store.cache_clear()
    scheduled_jobs = []
    monkeypatch.setattr(
        routes_upload,
        "schedule_document_processing",
        lambda background_tasks, document_id, stored_path: scheduled_jobs.append((document_id, stored_path)),
    )

    client = TestClient(create_app())
    pdf_text = " ".join(["The capital of France is Paris."] * 80)
    pdf_bytes = _build_pdf_bytes(pdf_text)

    response = client.post(
        "/api/upload",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["filename"] == "sample.pdf"
    assert payload["page_count"] == 0
    assert payload["chunk_count"] == 0
    assert payload["status"] == "processing"

    saved_path = Path(payload["stored_path"])
    assert saved_path.exists()
    assert saved_path.parent == upload_dir
    assert scheduled_jobs == [(payload["document_id"], saved_path)]

    store = DocumentStore(persist_directory=data_dir / "documents")
    record = store.get_document(payload["document_id"])
    assert record["status"] == "processing"

    get_settings.cache_clear()
    routes_upload.get_embed_service.cache_clear()
    routes_upload.get_vector_store.cache_clear()
    routes_upload.get_document_store.cache_clear()


class FakeEmbedService:
    def embed_texts(self, texts):
        vectors = []
        for text in texts:
            if "page two" in text.lower():
                vectors.append([0.0, 1.0])
            else:
                vectors.append([1.0, 0.0])
        return vectors


def test_upload_endpoint_indexes_chunks_in_vector_store(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    upload_dir = data_dir / "uploads"
    chroma_dir = data_dir / "chroma"

    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("CHROMA_DIR", str(chroma_dir))
    monkeypatch.setenv("DOCUMENTS_DIR", str(data_dir / "documents"))
    routes_upload.get_vector_store.cache_clear()
    routes_upload.get_document_store.cache_clear()
    monkeypatch.setattr(routes_upload, "get_embed_service", lambda: FakeEmbedService())
    get_settings.cache_clear()

    pdf_text = " ".join(["Retrieval augmented generation uses retrieved chunks."] * 80)
    pdf_bytes = _build_pdf_bytes(pdf_text)
    stored_path = upload_dir / "indexed.pdf"
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(pdf_bytes)
    document_id = "doc-indexed"
    store = DocumentStore(persist_directory=data_dir / "documents")
    store.create_document(
        document_id=document_id,
        filename="indexed.pdf",
        stored_path=stored_path,
        status="processing",
    )
    routes_upload.process_document(document_id, stored_path)

    store = VectorStore(persist_directory=chroma_dir)
    results = store.query(document_id=document_id, query_embedding=[1.0, 0.0], top_k=2)

    assert len(results) >= 1
    assert "Retrieval augmented generation" in results[0]["text"]
    metadata = DocumentStore(persist_directory=data_dir / "documents").get_document(document_id)
    assert metadata["status"] == "ready"
    assert metadata["chunk_count"] >= 1

    get_settings.cache_clear()
    routes_upload.get_vector_store.cache_clear()
    routes_upload.get_document_store.cache_clear()


def test_upload_endpoint_stores_page_number_per_chunk(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    upload_dir = data_dir / "uploads"
    chroma_dir = data_dir / "chroma"

    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("CHROMA_DIR", str(chroma_dir))
    monkeypatch.setenv("DOCUMENTS_DIR", str(data_dir / "documents"))
    routes_upload.get_vector_store.cache_clear()
    routes_upload.get_document_store.cache_clear()
    monkeypatch.setattr(routes_upload, "get_embed_service", lambda: FakeEmbedService())
    get_settings.cache_clear()

    pdf_bytes = _build_pdf_bytes(
        [
            "Page one covers general background and setup details.",
            "Page two contains the important answer about the final recommendation.",
        ]
    )
    stored_path = upload_dir / "pages.pdf"
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(pdf_bytes)
    document_id = "doc-pages"
    store = DocumentStore(persist_directory=data_dir / "documents")
    store.create_document(
        document_id=document_id,
        filename="pages.pdf",
        stored_path=stored_path,
        status="processing",
    )
    routes_upload.process_document(document_id, stored_path)

    store = VectorStore(persist_directory=chroma_dir)
    results = store.query(document_id=document_id, query_embedding=[0.0, 1.0], top_k=2)

    assert len(results) >= 1
    assert results[0]["page_number"] == 2
    assert "Page two contains" in results[0]["text"]

    get_settings.cache_clear()
    routes_upload.get_vector_store.cache_clear()
    routes_upload.get_document_store.cache_clear()


def test_document_status_endpoint_returns_indexing_state(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    document_dir = data_dir / "documents"

    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("UPLOAD_DIR", str(data_dir / "uploads"))
    monkeypatch.setenv("CHROMA_DIR", str(data_dir / "chroma"))
    monkeypatch.setenv("DOCUMENTS_DIR", str(document_dir))
    get_settings.cache_clear()
    routes_upload.get_document_store.cache_clear()

    store = DocumentStore(persist_directory=document_dir)
    store.create_document(
        document_id="doc-status",
        filename="queued.pdf",
        stored_path=data_dir / "uploads" / "queued.pdf",
        status="processing",
    )

    client = TestClient(create_app())
    response = client.get("/api/documents/doc-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == "doc-status"
    assert payload["status"] == "processing"

    get_settings.cache_clear()
    routes_upload.get_document_store.cache_clear()
