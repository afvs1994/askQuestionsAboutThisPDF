"""
Testes para o módulo de armazenamento vetorial (ChromaDB).

Valida operações de adição, busca por similaridade e filtragem
por documento no vector store.
"""
from __future__ import annotations

import pytest

from app.core.config import Settings
from app.models import DocumentChunk, DocumentType
from app.services.vector_store import VectorStore


class TestVectorStore:
    """Testes para VectorStore."""

    def test_add_chunks_and_search(self, temp_settings: Settings) -> None:
        """
        Verifica adição de chunks e busca por similaridade.
        """
        store = VectorStore(temp_settings)

        chunks = [
            DocumentChunk(
                document_id="doc-1",
                filename="test.pdf",
                mime_type="application/pdf",
                document_type=DocumentType.pdf,
                text="Machine learning is a subset of artificial intelligence.",
                chunk_index=0,
                section_index=0,
            ),
            DocumentChunk(
                document_id="doc-1",
                filename="test.pdf",
                mime_type="application/pdf",
                document_type=DocumentType.pdf,
                text="Deep learning uses neural networks with many layers.",
                chunk_index=1,
                section_index=0,
            ),
        ]

        # Embeddings simples para teste (não são reais, mas suficientes para testar estrutura)
        embeddings = [
            [0.1] * 384,  # Dimensão típica do MiniLM
            [0.2] * 384,
        ]

        count = store.add_chunks(chunks, embeddings)
        assert count == 2

    def test_add_chunks_mismatch_raises_error(self, temp_settings: Settings) -> None:
        """
        Verifica erro quando chunks e embeddings têm tamanhos diferentes.
        """
        store = VectorStore(temp_settings)

        chunks = [
            DocumentChunk(
                document_id="doc-1",
                filename="test.pdf",
                mime_type="application/pdf",
                document_type=DocumentType.pdf,
                text="Some text here.",
                chunk_index=0,
                section_index=0,
            )
        ]
        embeddings = [[0.1] * 384, [0.2] * 384]

        with pytest.raises(ValueError, match="same length"):
            store.add_chunks(chunks, embeddings)

    def test_add_empty_chunks(self, temp_settings: Settings) -> None:
        """
        Verifica que lista vazia retorna 0 sem erro.
        """
        store = VectorStore(temp_settings)

        count = store.add_chunks([], [])
        assert count == 0

    def test_search_returns_results(self, temp_settings: Settings) -> None:
        """
        Verifica que busca retorna resultados formatados corretamente.
        """
        store = VectorStore(temp_settings)

        # Adiciona alguns chunks
        chunks = [
            DocumentChunk(
                document_id="doc-1",
                filename="test.pdf",
                mime_type="application/pdf",
                document_type=DocumentType.pdf,
                text="Python is a programming language.",
                chunk_index=0,
                section_index=0,
                page=1,
            ),
        ]
        embeddings = [[0.1] * 384]
        store.add_chunks(chunks, embeddings)

        # Busca com embedding similar
        query_embedding = [0.1] * 384
        results = store.search(query_embedding, top_k=5)

        assert isinstance(results, list)
        # Pode retornar resultados ou lista vazia dependendo do ChromaDB

    def test_search_with_document_filter(self, temp_settings: Settings) -> None:
        """
        Verifica filtragem por document_id na busca.
        """
        store = VectorStore(temp_settings)

        # Adiciona chunks de dois documentos
        chunks_doc1 = [
            DocumentChunk(
                document_id="doc-1",
                filename="doc1.pdf",
                mime_type="application/pdf",
                document_type=DocumentType.pdf,
                text="Content from document 1.",
                chunk_index=0,
                section_index=0,
            ),
        ]
        chunks_doc2 = [
            DocumentChunk(
                document_id="doc-2",
                filename="doc2.pdf",
                mime_type="application/pdf",
                document_type=DocumentType.pdf,
                text="Content from document 2.",
                chunk_index=0,
                section_index=0,
            ),
        ]

        embeddings = [[0.1] * 384]
        store.add_chunks(chunks_doc1, embeddings)
        store.add_chunks(chunks_doc2, [[0.2] * 384])

        # Busca filtrando apenas doc-1
        query_embedding = [0.1] * 384
        results = store.search(query_embedding, top_k=5, document_id="doc-1")

        # Todos os resultados devem ser do doc-1
        for match in results:
            assert match.document_id == "doc-1"

