"""
Testes para o módulo de chunking.

Valida a divisão inteligente de textos em chunks, garantindo:
- Respeito ao tamanho máximo configurado
- Overlap entre chunks consecutivos
- Preservação de metadados de localização
"""
from __future__ import annotations

import pytest

from app.core.config import Settings
from app.models import DocumentSection, DocumentType
from app.services.chunking import _split_into_sentences, chunk_sections


class TestSplitIntoSentences:
    """Testes para a função de divisão em sentenças."""

    def test_simple_sentences(self) -> None:
        """
        Verifica divisão de sentenças simples.
        """
        text = "First sentence. Second sentence. Third sentence."
        sentences = _split_into_sentences(text)

        assert len(sentences) == 3
        assert sentences[0] == "First sentence."
        assert sentences[1] == "Second sentence."
        assert sentences[2] == "Third sentence."

    def test_question_and_exclamation(self) -> None:
        """
        Verifica que pontos de interrogação e exclamação são delimitadores.
        """
        text = "What is this? It is a test! Yes indeed."
        sentences = _split_into_sentences(text)

        assert len(sentences) == 3
        assert "What is this?" in sentences[0]
        assert "It is a test!" in sentences[1]

    def test_empty_text(self) -> None:
        """
        Verifica que texto vazio retorna lista vazia.
        """
        sentences = _split_into_sentences("")

        assert sentences == []

    def test_no_punctuation(self) -> None:
        """
        Verifica texto sem pontuação de fim de sentença.
        """
        text = "This is just one long sentence without ending punctuation"
        sentences = _split_into_sentences(text)

        assert len(sentences) == 1
        assert sentences[0] == text


class TestChunkSections:
    """Testes para a função principal de chunking."""

    def test_single_chunk_small_text(self, temp_settings: Settings) -> None:
        """
        Verifica que texto pequeno gera apenas um chunk.
        """
        section = DocumentSection(
            document_id="doc-1",
            filename="test.txt",
            mime_type="text/plain",
            document_type=DocumentType.pdf,
            text="This is a short text.",
            section_index=0,
            page=1,
        )

        chunks = chunk_sections([section], temp_settings)

        assert len(chunks) == 1
        assert chunks[0].text == "This is a short text."
        assert chunks[0].document_id == "doc-1"
        assert chunks[0].page == 1

    def test_multiple_chunks_large_text(self, temp_settings: Settings) -> None:
        """
        Verifica que texto grande é dividido em múltiplos chunks.
        """
        # Cria um texto com sentenças repetidas que excedem chunk_size_chars (500)
        sentences = [f"This is sentence number {i} with some extra words to make it longer." for i in range(20)]
        text = " ".join(sentences)

        section = DocumentSection(
            document_id="doc-1",
            filename="test.txt",
            mime_type="text/plain",
            document_type=DocumentType.pdf,
            text=text,
            section_index=0,
        )

        chunks = chunk_sections([section], temp_settings)

        assert len(chunks) > 1
        # Verifica que cada chunk está dentro do limite (com tolerância para a última sentença)
        for chunk in chunks:
            assert len(chunk.text) <= temp_settings.chunk_size_chars + 100

    def test_overlap_between_chunks(self, temp_settings: Settings) -> None:
        """
        Verifica que há overlap configurável entre chunks consecutivos.
        """
        temp_settings.chunk_overlap_sentences = 1
        sentences = [f"Sentence {i} is here with enough words." for i in range(15)]
        text = " ".join(sentences)

        section = DocumentSection(
            document_id="doc-1",
            filename="test.txt",
            mime_type="text/plain",
            document_type=DocumentType.pdf,
            text=text,
            section_index=0,
        )

        chunks = chunk_sections([section], temp_settings)

        if len(chunks) > 1:
            # Verifica que há overlap (a última sentença do chunk anterior
            # deve aparecer no início do próximo)
            first_chunk_sentences = _split_into_sentences(chunks[0].text)
            second_chunk_sentences = _split_into_sentences(chunks[1].text)
            assert any(s in second_chunk_sentences for s in first_chunk_sentences[-1:])

    def test_preserves_metadata(self, temp_settings: Settings) -> None:
        """
        Verifica que metadados de localização são preservados nos chunks.
        """
        section = DocumentSection(
            document_id="doc-1",
            filename="test.xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            document_type=DocumentType.xlsx,
            text="Some spreadsheet content here.",
            section_index=2,
            sheet="Sheet1",
            row_start=5,
            row_end=10,
        )

        chunks = chunk_sections([section], temp_settings)

        assert len(chunks) == 1
        assert chunks[0].sheet == "Sheet1"
        assert chunks[0].section_index == 2
        assert chunks[0].row_start == 5
        assert chunks[0].row_end == 10

    def test_empty_sections(self, temp_settings: Settings) -> None:
        """
        Verifica que seções vazias não geram chunks.
        """
        chunks = chunk_sections([], temp_settings)

        assert chunks == []

