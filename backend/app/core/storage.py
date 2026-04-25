from __future__ import annotations

import json
import re
from pathlib import Path
from threading import Lock
from typing import Sequence

from app.core.config import Settings
from app.models import StoredDocument

_FILENAME_SANITIZER = re.compile(r"[^A-Za-z0-9._-]+")


class DocumentStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.data_dir = settings.data_dir
        self.upload_dir = settings.upload_dir
        self.chroma_dir = settings.chroma_dir
        self.registry_file = settings.registry_file
        self._lock = Lock()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

    def save_original_file(self, document_id: str, filename: str, content: bytes) -> Path:
        safe_filename = self._sanitize_filename(filename)
        document_dir = self.upload_dir / document_id
        document_dir.mkdir(parents=True, exist_ok=True)
        target_path = document_dir / safe_filename
        target_path.write_bytes(content)
        return target_path

    def list_documents(self) -> list[StoredDocument]:
        documents = self._load_documents()
        return sorted(documents, key=lambda document: document.created_at, reverse=True)

    def get_document(self, document_id: str) -> StoredDocument | None:
        for document in self._load_documents():
            if document.id == document_id:
                return document
        return None

    def upsert_document(self, document: StoredDocument) -> None:
        with self._lock:
            documents = self._load_documents()
            kept_documents = [existing for existing in documents if existing.id != document.id]
            kept_documents.append(document)
            kept_documents.sort(key=lambda item: item.created_at, reverse=True)
            self._write_documents(kept_documents)

    def _load_documents(self) -> list[StoredDocument]:
        if not self.registry_file.exists():
            return []
        raw_text = self.registry_file.read_text(encoding="utf-8").strip()
        if not raw_text:
            return []
        payload = json.loads(raw_text)
        if not isinstance(payload, list):
            raise RuntimeError(f"Document registry is malformed: {self.registry_file}")
        documents: list[StoredDocument] = []
        for item in payload:
            if isinstance(item, dict):
                documents.append(StoredDocument.model_validate(item))
        return documents

    def _write_documents(self, documents: Sequence[StoredDocument]) -> None:
        payload = [document.model_dump(mode="json") for document in documents]
        temp_path = self.registry_file.with_suffix(self.registry_file.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.registry_file)

    def _sanitize_filename(self, filename: str) -> str:
        clean_name = Path(filename).name.strip()
        if not clean_name:
            clean_name = "upload"
        return _FILENAME_SANITIZER.sub("_", clean_name)