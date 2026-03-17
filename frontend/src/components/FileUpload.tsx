import type { ChangeEvent } from 'react';

type FileUploadProps = {
  isUploading: boolean;
  onFileSelect: (file: File | null) => void;
  selectedFileName: string | null;
  uploadMessage: string;
};

export function FileUpload({
  isUploading,
  onFileSelect,
  selectedFileName,
  uploadMessage,
}: FileUploadProps) {
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    onFileSelect(event.target.files?.[0] ?? null);
  }

  return (
    <section className="panel hero-panel">
      <div className="eyebrow">Local RAG Workspace</div>
      <h1>Upload a PDF and ask grounded questions about what it actually says.</h1>
      <p className="hero-copy">
        Text is extracted, chunked, embedded into Chroma, and answered through Ollama using
        <code> mistral:latest</code>.
      </p>
      <label className="upload-card">
        <span className="upload-label">{selectedFileName ?? 'Choose a PDF to index locally'}</span>
        <input
          type="file"
          accept="application/pdf"
          onChange={handleChange}
          disabled={isUploading}
        />
      </label>
      <p className="status-line">{uploadMessage}</p>
    </section>
  );
}
