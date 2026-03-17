import type { FormEvent } from 'react';

import type { QueryResponse } from '../api/client';
import { SourceChunks } from './SourceChunks';

export type ChatEntry = {
  id: string;
  question: string;
  response: QueryResponse;
};

type ChatPanelProps = {
  canAsk: boolean;
  question: string;
  isAsking: boolean;
  askError: string;
  chatEntries: ChatEntry[];
  onQuestionChange: (value: string) => void;
  onSubmit: () => void;
};

export function ChatPanel({
  canAsk,
  question,
  isAsking,
  askError,
  chatEntries,
  onQuestionChange,
  onSubmit,
}: ChatPanelProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">Document Q&A</div>
          <h2>Ask a direct question and inspect the retrieved evidence.</h2>
        </div>
      </div>

      <form className="ask-form" onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          placeholder="Example: What are the key eligibility requirements in this document?"
          disabled={!canAsk || isAsking}
          rows={4}
        />
        <button type="submit" disabled={!canAsk || isAsking || question.trim().length === 0}>
          {isAsking ? 'Searching and answering...' : 'Ask the PDF'}
        </button>
      </form>

      {askError ? <p className="error-line">{askError}</p> : null}
      {!canAsk ? <p className="status-line">Upload a PDF before asking questions.</p> : null}

      <div className="conversation">
        {chatEntries.map((entry) => (
          <article key={entry.id} className="answer-card">
            <p className="question-badge">Q</p>
            <p className="question-copy">{entry.question}</p>
            <div className="answer-shell">
              <p className="answer-badge">A</p>
              <div>
                <p className="answer-copy">{entry.response.answer}</p>
                <p className="meta-line">
                  Model: <code>{entry.response.model}</code> • Context chunks:{' '}
                  {entry.response.prompt_context_count}
                </p>
                <SourceChunks sources={entry.response.sources} />
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
