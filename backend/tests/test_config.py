"""
Testes para o módulo de configurações.

Valida o carregamento de configurações, validadores de campo
e comportamento padrão das settings.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings


class TestSettings:
    """Testes para a classe Settings."""

    def test_default_values(self) -> None:
        """
        Verifica que os valores padrão são aplicados corretamente.
        """
        settings = Settings()

        assert settings.app_name == "Private Document RAG API"
        assert settings.api_prefix == "/api"
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.ollama_model == "llama3.1"
        assert settings.chunk_size_chars == 1800
        assert settings.chunk_overlap_sentences == 1
        assert settings.top_k_default == 5
        assert settings.chroma_collection_name == "rag_chunks"

    def test_cors_origins_from_string(self) -> None:
        """
        Verifica que CORS origins são parseados corretamente de string.
        """
        settings = Settings(cors_origins="http://localhost:3000,http://localhost:5173")

        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]

    def test_cors_origins_from_list(self) -> None:
        """
        Verifica que CORS origins aceitam lista diretamente.
        """
        settings = Settings(cors_origins=["http://example.com", "http://test.com"])

        assert settings.cors_origins == ["http://example.com", "http://test.com"]

    def test_cors_origins_none_fallback(self) -> None:
        """
        Verifica que None usa o valor padrão de CORS origins.
        """
        settings = Settings(cors_origins=None)

        assert settings.cors_origins == ["http://localhost:5173"]

    def test_cors_origins_empty_string_fallback(self) -> None:
        """
        Verifica que string vazia usa o valor padrão.
        """
        settings = Settings(cors_origins="")

        assert settings.cors_origins == ["http://localhost:5173"]

    def test_custom_values(self, temp_settings: Settings) -> None:
        """
        Verifica que valores customizados são aplicados.
        """
        assert temp_settings.chunk_size_chars == 500
        assert temp_settings.top_k_default == 3

