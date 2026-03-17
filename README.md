# PDF Assistant RAG

Local PDF question answering with FastAPI, React, ChromaDB, sentence-transformers, and Ollama.

This project lets you upload a PDF, chunk and embed its contents, retrieve the most relevant passages for a question, and generate an answer grounded in those passages. The current setup is local-first and single-user.

## Features

- Upload PDFs through a React frontend
- Extract and chunk PDF text on the backend
- Store embeddings in a local ChromaDB database
- Retrieve relevant source chunks for a question
- Generate grounded answers through Ollama
- Run backend tests for the ingestion and query flow

## Stack

- Backend: FastAPI, PyPDF, ChromaDB, sentence-transformers, Uvicorn
- Frontend: React 19, TypeScript, Vite
- Local LLM runtime: Ollama

## Repository Layout

- `backend/` FastAPI API, PDF ingestion, embeddings, retrieval, tests
- `frontend/` React UI for upload and chat
- `docs/` implementation plan and manual test notes

## Prerequisites

- Python 3.11+
- Node.js 20+
- Ollama running locally at `http://localhost:11434`
- A chat model pulled in Ollama, for example `mistral:latest`

## Quick Start

### 1. Start the backend

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

The backend listens on `http://127.0.0.1:8000` by default.

### 2. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs on `http://127.0.0.1:5173`.

### 3. Ask questions about a PDF

1. Open the frontend in your browser.
2. Upload a PDF.
3. Ask a factual question about the uploaded document.
4. Review the answer together with the retrieved source chunks.

## Configuration

Configuration is loaded from `.env` at the repository root. A starter file is included in `.env.example`.

Supported settings:

- `APP_NAME`
- `API_PREFIX`
- `DATA_DIR`
- `UPLOAD_DIR`
- `CHROMA_DIR`
- `DOCUMENTS_DIR`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `EMBEDDING_MODEL`

## Development

### Run tests

```powershell
.\.venv\Scripts\python -m pytest backend\tests -v
```

### Build the frontend

```powershell
cd frontend
npm run build
```

### Manual testing

See `docs/testing-manual.md` for a basic end-to-end smoke test.

## Current Limitations

- No OCR for scanned PDFs
- Local single-user workflow only
- Retrieval quality depends on chunking, embeddings, and prompt grounding
- Large PDFs may take longer to ingest and embed

## License

MIT. See `LICENSE`.
