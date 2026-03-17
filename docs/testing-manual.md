# Manual Testing

## Start Backend

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload
```

## Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Test Flow

1. Open `http://127.0.0.1:5173`.
2. Upload `backend/tests/fixtures/sample.pdf`.
3. Ask:
   - `What is the capital of France?`
   - `What serves the API?`
   - `What does the document say about Germany?`
4. Confirm answers include retrieved source chunks and that unsupported questions are declined.
