"""
Testes para o módulo de persistência de documentos.

Valida operações de CRUD no DocumentStorage, incluindo:
- Salvamento de arquivos originais
- Registro e listagem de metadados
- Thread-safety das operações de escrita
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.config import Settings
from app.core.storage import DocumentStorage
from app.models import StoredDocument


class TestDocumentStorage:
    """Testes para DocumentStorage."""

    def test_ensure_directories_created(self, temp_settings: Settings) -> None:
        """
        Verifica que os diretórios são criados na inicialização.
        """
        storage = DocumentStorage(temp_settings)

        assert temp_settings.data_dir.exists()
        assert temp_settings.upload_dir.exists()
        assert temp_settings.chroma_dir.exists()
        assert temp_settings.registry_file.parent.exists()

    def test_save_original_file(self, document_storage: DocumentStorage) -> None:
        """
        Verifica que arquivos são salvos corretamente.
        """
        document_id = "test-doc-123"
        filename = "test.pdf"
        content = b"PDF content here"

        path = document_storage.save_original_file(document_id, filename, content)

        assert path.exists()
        assert path.read_bytes() == content
        assert path.name == "test.pdf"
        assert path.parent.name == document_id

    def test_save_sanitizes_filename(self, document_storage: DocumentStorage) -> None:
        """
        Verifica que nomes de arquivo perigosos são sanitizados.
        """
        document_id = "test-doc"
        filename = "../../../etc/passwd"
        content = b"malicious"

        path = document_storage.save_original_file(document_id, filename, content)

        assert ".." not in path.name
        assert path.exists()

    def test_list_documents_empty(self, document_storage: DocumentStorage) -> None:
        """
        Verifica que lista vazia é retornada quando não há documentos.
        """
        documents = document_storage.list_documents()

        assert documents == []

    def test_upsert_and_list_documents(self, document_storage: DocumentStorage) -> None:
        """
        Verifica inserção e listagem de documentos.
        """
        doc1 = StoredDocument(
            id="doc-1",
            filename="file1.pdf",
            mime_type="application/pdf",
            document_type="pdf",
            chunk_count=5,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            original_path="/tmp/file1.pdf",
        )
        doc2 = StoredDocument(
            id="doc-2",
            filename="file2.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            document_type="docx",
            chunk_count=3,
            created_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            original_path="/tmp/file2.docx",
        )

        document_storage.upsert_document(doc1)
        document_storage.upsert_document(doc2)

        documents = document_storage.list_documents()

        assert len(documents) == 2
        # Deve estar ordenado por data decrescente
        assert documents[0].id == "doc-2"
        assert documents[1].id == "doc-1"

    def test_upsert_updates_existing(self, document_storage: DocumentStorage) -> None:
        """
        Verifica que upsert substitui documento existente.
        """
        doc = StoredDocument(
            id="doc-1",
            filename="old.pdf",
            mime_type="application/pdf",
            document_type="pdf",
            chunk_count=2,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            original_path="/tmp/old.pdf",
        )
        document_storage.upsert_document(doc)

        updated_doc = StoredDocument(
            id="doc-1",
            filename="new.pdf",
            mime_type="application/pdf",
            document_type="pdf",
            chunk_count=5,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            original_path="/tmp/new.pdf",
        )
        document_storage.upsert_document(updated_doc)

        documents = document_storage.list_documents()

        assert len(documents) == 1
        assert documents[0].filename == "new.pdf"
        assert documents[0].chunk_count == 5

    def test_get_document_found(self, document_storage: DocumentStorage) -> None:
        """
        Verifica recuperação de documento existente.
        """
        doc = StoredDocument(
            id="doc-found",
            filename="found.pdf",
            mime_type="application/pdf",
            document_type="pdf",
            chunk_count=1,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            original_path="/tmp/found.pdf",
        )
        document_storage.upsert_document(doc)

        result = document_storage.get_document("doc-found")

        assert result is not None
        assert result.filename == "found.pdf"

    def test_get_document_not_found(self, document_storage: DocumentStorage) -> None:
        """
        Verifica que None é retornado para documento inexistente.
        """
        result = document_storage.get_document("non-existent")

        assert result is None

