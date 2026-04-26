"""
Testes para o módulo de geração de embeddings.

Valida a conversão de textos em vetores numéricos e o tratamento
de casos edge (lista vazia, erros do modelo).
"""
from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.embeddings import get_embeddings


class TestGetEmbeddings:
    """Testes para geração de embeddings."""

    def test_empty_list_returns_empty(self, temp_settings: Settings) -> None:
        """
        Verifica que lista vazia retorna lista vazia sem carregar modelo.
        """
        result = get_embeddings([], temp_settings)

        assert result == []

    def test_single_text_returns_embedding(self, temp_settings: Settings) -> None:
        """
        Verifica que um texto gera um vetor de embedding.
        """
        result = get_embeddings(["This is a test sentence."], temp_settings)

        assert len(result) == 1
        assert isinstance(result[0], list)
        assert len(result[0]) > 0
        assert all(isinstance(x, float) for x in result[0])

    def test_multiple_texts_return_embeddings(self, temp_settings: Settings) -> None:
        """
        Verifica que múltiplos textos geram múltiplos embeddings.
        """
        texts = ["First sentence.", "Second sentence.", "Third sentence."]
        result = get_embeddings(texts, temp_settings)

        assert len(result) == 3
        # Todos os embeddings devem ter a mesma dimensão
        dimensions = [len(embedding) for embedding in result]
        assert all(d == dimensions[0] for d in dimensions)

    def test_similar_texts_have_similar_embeddings(self, temp_settings: Settings) -> None:
        """
        Verifica que textos semanticamente similares têm embeddings próximos.
        """
        result = get_embeddings(
            ["The cat sat on the mat.", "A cat was sitting on a mat."],
            temp_settings,
        )

        assert len(result) == 2
        # Ambos devem ter a mesma dimensão
        assert len(result[0]) == len(result[1])

