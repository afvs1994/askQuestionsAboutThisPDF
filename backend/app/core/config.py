"""
Configurações da aplicação via variáveis de ambiente.

Utiliza pydantic-settings para carregar configurações de um arquivo .env
com valores padrão sensatos para desenvolvimento local.
Todas as configurações são cacheadas via lru_cache para evitar
releituras desnecessárias.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Diretório base do projeto (3 níveis acima deste arquivo: app/core/config.py)
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Configurações centralizadas da aplicação.

    Carrega valores do arquivo .env na raiz do backend, com fallbacks
    para desenvolvimento local. Inclui configurações de:
    - Aplicação (nome, prefixo da API)
    - Diretórios (dados, uploads, chroma)
    - CORS (origens permitidas)
    - Modelos (embedding, LLM via Ollama)
    - Processamento (tamanho de chunks, overlap)
    """
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Private Document RAG API"
    api_prefix: str = "/api"
    data_dir: Path = Field(default_factory=lambda: BASE_DIR / "data")
    upload_dir: Path = Field(default_factory=lambda: BASE_DIR / "data" / "uploads")
    chroma_dir: Path = Field(default_factory=lambda: BASE_DIR / "data" / "chroma")
    registry_file: Path = Field(default_factory=lambda: BASE_DIR / "data" / "documents.json")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_timeout_seconds: float = 60.0
    chunk_size_chars: int = 1800
    chunk_overlap_sentences: int = 1
    top_k_default: int = 5
    chroma_collection_name: str = "rag_chunks"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        """
        Valida e converte a configuração de CORS origins.

        Aceita:
        - None (usa padrão)
        - String com múltiplas origins separadas por vírgula
        - Lista de strings

        Args:
            value: Valor bruto da variável de ambiente

        Returns:
            Lista de origins sanitizadas
        """
        if value is None:
            return ["http://localhost:5173"]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ["http://localhost:5173"]
            origins = [item.strip() for item in stripped.split(",")]
            return [origin for origin in origins if origin]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return ["http://localhost:5173"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retorna a instância cacheada das configurações.

    O cache garante que as configurações sejam lidas apenas uma vez,
    melhorando a performance em requisições subsequentes.

    Returns:
        Instância de Settings com valores carregados
    """
    return Settings()

