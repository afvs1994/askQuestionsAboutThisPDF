"""
Testes para os schemas Pydantic da API.

Valida a serialização, desserialização e validação de dados
nos modelos de requisição e resposta.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import ChatRequest, DocumentSummary
from app.models import DocumentType


class TestChatRequest:
    """Testes para o schema de requisição de chat."""

    def test_valid_request(self) -> None:
        """
        Verifica criação de requisição válida.
        """
        request = ChatRequest(question="What is AI?")

        assert request.question == "What is AI?"
        assert request.document_id is None
        assert request.top_k == 5

    def test_question_gets_stripped(self) -> None:
        """
        Verifica que espaços em branco são removidos da pergunta.
        """
        request = ChatRequest(question="  What is AI?  ")

        assert request.question == "What is AI?"

    def test_empty_question_raises_error(self) -> None:
        """
        Verifica que pergunta vazia lança erro de validação.
        """
        with pytest.raises(ValidationError):
            ChatRequest(question="")

    def test_whitespace_only_question_raises_error(self) -> None:
        """
        Verifica que pergunta com apenas espaços lança erro.
        """
        with pytest.raises(ValidationError):
            ChatRequest(question="   ")

    def test_document_id_normalized(self) -> None:
        """
        Verifica que document_id vazio é convertido para None.
        """
        request = ChatRequest(question="Test?", document_id="")

        assert request.document_id is None

    def test_document_id_stripped(self) -> None:
        """
        Verifica que espaços são removidos do document_id.
        """
        request = ChatRequest(question="Test?", document_id="  doc-123  ")

        assert request.document_id == "doc-123"

    def test_top_k_within_range(self) -> None:
        """
        Verifica que top_k dentro do range é aceito.
        """
        request = ChatRequest(question="Test?", top_k=10)

        assert request.top_k == 10

    def test_top_k_too_low_raises_error(self) -> None:
        """
        Verifica que top_k < 1 lança erro.
        """
        with pytest.raises(ValidationError):
            ChatRequest(question="Test?", top_k=0)

    def test_top_k_too_high_raises_error(self) -> None:
        """
        Verifica que top_k > 20 lança erro.
        """
        with pytest.raises(ValidationError):
            ChatRequest(question="Test?", top_k=21)


class TestDocumentSummary:
    """Testes para o schema de resumo de documento."""

    def test_valid_summary(self) -> None:
        """
        Verifica criação de resumo válido.
        """
        from datetime import datetime, timezone

        summary = DocumentSummary(
            id="doc-1",
            filename="test.pdf",
            mime_type="application/pdf",
            document_type=DocumentType.pdf,
            chunk_count=5,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert summary.id == "doc-1"
        assert summary.filename == "test.pdf"
        assert summary.chunk_count == 5

