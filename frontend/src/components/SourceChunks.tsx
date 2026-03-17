import type { SourceChunk } from '../api/client';

type SourceChunksProps = {
  sources: SourceChunk[];
};

export function SourceChunks({ sources }: SourceChunksProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <section className="source-list">
      {sources.map((source, index) => (
        <article key={`${source.page_number}-${source.chunk_index}-${index}`} className="source-card">
          <header className="source-header">
            <span>Page {source.page_number}</span>
            <span>Chunk {source.chunk_index}</span>
          </header>
          <p>{source.text}</p>
        </article>
      ))}
    </section>
  );
}
