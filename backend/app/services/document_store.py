import json
from pathlib import Path
from typing import Any


class DocumentStore:
    def __init__(self, persist_directory: Path) -> None:
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

    def _document_path(self, document_id: str) -> Path:
        return self.persist_directory / f"{document_id}.json"

    def create_document(
        self,
        document_id: str,
        filename: str,
        stored_path: Path,
        status: str,
        page_count: int = 0,
        chunk_count: int = 0,
    ) -> dict[str, Any]:
        record = {
            "document_id": document_id,
            "filename": filename,
            "stored_path": str(Path(stored_path)),
            "status": status,
            "page_count": page_count,
            "chunk_count": chunk_count,
        }
        self._document_path(document_id).write_text(json.dumps(record), encoding="utf-8")
        return record

    def get_document(self, document_id: str) -> dict[str, Any]:
        document_path = self._document_path(document_id)
        if not document_path.exists():
            raise FileNotFoundError(document_id)

        return json.loads(document_path.read_text(encoding="utf-8"))

    def update_document(self, document_id: str, **updates: Any) -> dict[str, Any]:
        record = self.get_document(document_id)
        record.update(updates)
        self._document_path(document_id).write_text(json.dumps(record), encoding="utf-8")
        return record
