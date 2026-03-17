# PDF RAG Assistant Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local PDF question-answering assistant that ingests PDFs, stores semantic chunks in ChromaDB, retrieves relevant context for a question, and answers with Mistral through Ollama.

**Architecture:** Use a two-app layout: `backend/` for FastAPI, ingestion, embeddings, and retrieval; `frontend/` for the Vite + React UI. Keep the first version single-user and local-first. PDF ingestion writes extracted text and chunk metadata once, Chroma persists embeddings locally, and queries retrieve top-k chunks before calling Ollama.

**Tech Stack:** FastAPI, Python 3.11+, PyPDF, sentence-transformers (`all-MiniLM-L6-v2`), ChromaDB, Ollama (`mistral`), React, Vite, TypeScript.

---

## Refined Product Scope

### Recommended V1
- Single-user local app
- Upload one PDF at a time, with support for multiple uploaded documents later
- Ask natural-language questions and show grounded answers plus cited chunks
- No auth, no cloud storage, no user accounts, no streaming persistence across devices

### Avoid in V1
- OCR for scanned PDFs
- Multi-user workspaces
- Complex agent workflows
- Hybrid search, rerankers, and feedback loops

## Proposed Repository Layout

- `backend/app/main.py`
- `backend/app/api/routes_upload.py`
- `backend/app/api/routes_query.py`
- `backend/app/core/config.py`
- `backend/app/services/pdf_service.py`
- `backend/app/services/chunk_service.py`
- `backend/app/services/embed_service.py`
- `backend/app/services/vector_store.py`
- `backend/app/services/llm_service.py`
- `backend/app/models/schemas.py`
- `backend/tests/`
- `frontend/src/api/client.ts`
- `frontend/src/components/FileUpload.tsx`
- `frontend/src/components/ChatPanel.tsx`
- `frontend/src/components/SourceChunks.tsx`
- `frontend/src/App.tsx`

## API Shape

### `POST /api/upload`
- Input: multipart `file`
- Output: `document_id`, filename, page count, chunk count, status

### `POST /api/query`
- Input: `document_id`, `question`, optional `top_k`
- Output: answer text, retrieved chunks, similarity scores, model metadata

### `GET /api/health`
- Check FastAPI, Chroma path, embedding model load, and Ollama connectivity

## Data Flow

1. Upload PDF.
2. Extract text page-by-page with PyPDF.
3. Clean whitespace and split into overlapping chunks.
4. Embed each chunk with `all-MiniLM-L6-v2`.
5. Store chunk text, page number, and document metadata in Chroma.
6. Embed the user question.
7. Retrieve top-k chunks from Chroma.
8. Build a grounded prompt with retrieved context.
9. Send prompt to Ollama Mistral.
10. Return answer and source chunks to the frontend.

## Key Design Decisions

### Chunking
- Start with 700-900 characters and 100-150 character overlap.
- Store page number and chunk index for citations.
- Keep chunking deterministic so re-ingestion is reproducible.

### Prompting
- Instruct the model to answer only from retrieved context.
- If context is insufficient, it must say so.
- Return source excerpts with page references in the API response.

### Storage
- Persist Chroma under `backend/data/chroma/`.
- Store uploaded PDFs in `backend/data/uploads/`.
- Keep document metadata in Chroma first; add SQLite only if needed.

## Task Plan

### Task 1: Scaffold backend

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/models/schemas.py`
- Create: `backend/tests/test_health.py`

**Steps:**
1. Create a FastAPI app with `/api/health`.
2. Add config for upload path, Chroma path, Ollama base URL, and model names.
3. Write a failing test for `/api/health`.
4. Implement the endpoint and run `pytest backend/tests -v`.

### Task 2: Build ingestion pipeline

**Files:**
- Create: `backend/app/api/routes_upload.py`
- Create: `backend/app/services/pdf_service.py`
- Create: `backend/app/services/chunk_service.py`
- Create: `backend/tests/test_upload.py`

**Steps:**
1. Write tests for PDF upload, extraction, and chunk count.
2. Implement PDF text extraction and deterministic chunking.
3. Save uploaded PDFs to disk.
4. Return ingestion metadata from `POST /api/upload`.

### Task 3: Add embeddings and vector storage

**Files:**
- Create: `backend/app/services/embed_service.py`
- Create: `backend/app/services/vector_store.py`
- Create: `backend/tests/test_vector_store.py`

**Steps:**
1. Write tests for embedding generation and Chroma insert/query flow.
2. Load `all-MiniLM-L6-v2` once at startup or on first use.
3. Upsert chunk embeddings with document and page metadata.
4. Verify retrieval order with a small fixture PDF.

### Task 4: Add RAG query endpoint

**Files:**
- Create: `backend/app/api/routes_query.py`
- Create: `backend/app/services/llm_service.py`
- Create: `backend/tests/test_query.py`

**Steps:**
1. Write tests for query request validation and empty-context behavior.
2. Implement top-k retrieval from Chroma.
3. Build the grounded prompt for Ollama Mistral.
4. Return answer text plus retrieved source chunks.

### Task 5: Scaffold frontend

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/components/FileUpload.tsx`
- Create: `frontend/src/components/ChatPanel.tsx`
- Create: `frontend/src/components/SourceChunks.tsx`
- Create: `frontend/src/App.tsx`

**Steps:**
1. Create a basic Vite React TypeScript app.
2. Add PDF upload UI and upload status handling.
3. Add question input, answer panel, and source chunk display.
4. Show loading, error, and no-document states cleanly.

### Task 6: End-to-end verification

**Files:**
- Create: `backend/tests/fixtures/sample.pdf`
- Create: `docs/testing-manual.md`

**Steps:**
1. Run backend tests with `pytest backend/tests -v`.
2. Run frontend checks with `npm run build`.
3. Manually upload a sample PDF and ask 3-5 factual questions.
4. Confirm answers are grounded, cited, and decline unsupported questions.

## Risks and Next Improvements

- Scanned PDFs will fail without OCR.
- Long PDFs may need batching and background ingestion.
- Basic semantic retrieval may miss exact keyword matches.
- Mistral prompt quality will matter more than model size for V1.

## Recommended Milestones

1. Backend ingestion working with one sample PDF
2. Retrieval returning relevant chunks
3. Ollama answer generation grounded in retrieved context
4. Frontend upload and chat flow complete
5. Manual evaluation with real documents
