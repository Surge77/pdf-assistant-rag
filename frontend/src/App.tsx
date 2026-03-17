import { startTransition, useState } from 'react';

import { askQuestion, uploadPdf, type QueryResponse, type UploadResponse } from './api/client';
import { ChatPanel, type ChatEntry } from './components/ChatPanel';
import { FileUpload } from './components/FileUpload';
import './styles.css';

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [uploadMessage, setUploadMessage] = useState('No document indexed yet.');
  const [uploadError, setUploadError] = useState('');
  const [question, setQuestion] = useState('');
  const [askError, setAskError] = useState('');
  const [chatEntries, setChatEntries] = useState<ChatEntry[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);

  async function handleFileSelect(file: File | null) {
    setSelectedFile(file);
    setUploadError('');

    if (!file) {
      return;
    }

    setIsUploading(true);
    setUploadMessage('Extracting text, creating chunks, and indexing embeddings...');

    try {
      const result = await uploadPdf(file);
      startTransition(() => {
        setUploadResult(result);
        setChatEntries([]);
        setUploadMessage(
          `${result.filename} indexed: ${result.page_count} page(s), ${result.chunk_count} chunks.`
        );
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed.';
      setUploadError(message);
      setUploadMessage('Upload failed. Check the backend and try again.');
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAsk() {
    if (!uploadResult || question.trim().length === 0) {
      return;
    }

    setIsAsking(true);
    setAskError('');
    const currentQuestion = question.trim();

    try {
      const response = await askQuestion(uploadResult.document_id, currentQuestion);
      const entry: ChatEntry = {
        id: `${Date.now()}`,
        question: currentQuestion,
        response: response as QueryResponse,
      };
      startTransition(() => {
        setChatEntries((currentEntries) => [entry, ...currentEntries]);
        setQuestion('');
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Question failed.';
      setAskError(message);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="background-orb background-orb-left" />
      <div className="background-orb background-orb-right" />
      <div className="layout">
        <FileUpload
          isUploading={isUploading}
          onFileSelect={handleFileSelect}
          selectedFileName={selectedFile?.name ?? uploadResult?.filename ?? null}
          uploadMessage={uploadError || uploadMessage}
        />
        <ChatPanel
          canAsk={uploadResult !== null}
          question={question}
          isAsking={isAsking}
          askError={askError}
          chatEntries={chatEntries}
          onQuestionChange={setQuestion}
          onSubmit={handleAsk}
        />
      </div>
    </main>
  );
}
