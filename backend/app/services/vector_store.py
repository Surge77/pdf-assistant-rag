from pathlib import Path
from typing import Any

import chromadb


class VectorStore:
    def __init__(self, persist_directory: Path, collection_name: str = "pdf_chunks") -> None:
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert_chunks(self, document_id: str, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return

        self.collection.upsert(
            ids=[chunk["chunk_id"] for chunk in chunks],
            documents=[chunk["text"] for chunk in chunks],
            embeddings=[chunk["embedding"] for chunk in chunks],
            metadatas=[
                {
                    "document_id": document_id,
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                }
                for chunk in chunks
            ],
        )

    def query(self, document_id: str, query_embedding: list[float], top_k: int = 4) -> list[dict[str, Any]]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"document_id": document_id},
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        formatted_results: list[dict[str, Any]] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            formatted_results.append(
                {
                    "text": document,
                    "page_number": metadata["page_number"],
                    "chunk_index": metadata["chunk_index"],
                    "score": distance,
                }
            )

        return formatted_results
