export type UploadResponse = {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  status: string;
  stored_path: string;
};

export type SourceChunk = {
  text: string;
  page_number: number;
  chunk_index: number;
  score: number;
};

export type QueryResponse = {
  answer: string;
  model: string;
  prompt_context_count: number;
  sources: SourceChunk[];
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  return parseResponse<UploadResponse>(response);
}

export async function askQuestion(documentId: string, question: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      document_id: documentId,
      question,
    }),
  });

  return parseResponse<QueryResponse>(response);
}
