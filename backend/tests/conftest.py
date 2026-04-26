"""
Fixtures e configurações compartilhadas para todos os testes.

Fornece fixtures pytest reutilizáveis para:
- Configurações de teste (diretórios temporários)
- Cliente HTTP para testes de API
- Instâncias de serviços mockados
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.storage import DocumentStorage
from app.services.vector_store import VectorStore


@pytest.fixture
def temp_settings() -> Settings:
    """
    Cria configurações com diretórios temporários para testes.

    Garante que os testes não poluam o filesystem do projeto
    e que cada teste tenha um ambiente limpo e isolado.
    """
    # ignore_cleanup_errors=True necessário no Windows porque o ChromaDB
    # mantém handles de arquivo abertos, impedindo a exclusão do temp dir
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        settings = Settings(
            data_dir=temp_path / "data",
            upload_dir=temp_path / "data" / "uploads",
            chroma_dir=temp_path / "data" / "chroma",
            registry_file=temp_path / "data" / "documents.json",
            embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            ollama_base_url="http://localhost:11434",
            ollama_model="llama3.1",
            chunk_size_chars=500,
            chunk_overlap_sentences=1,
            top_k_default=3,
        )
        yield settings


@pytest.fixture
def document_storage(temp_settings: Settings) -> DocumentStorage:
    """
    Cria um DocumentStorage com diretório temporário.
    """
    return DocumentStorage(temp_settings)


@pytest.fixture
def vector_store(temp_settings: Settings) -> VectorStore:
    """
    Cria um VectorStore com diretório temporário.
    """
    return VectorStore(temp_settings)

