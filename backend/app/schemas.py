"""
Schemas Pydantic para requisições e respostas da API REST.

Separa os modelos de domínio (models.py) dos contratos da API,
permitindo evolução independente e validação automática de
entrada/saída pelo FastAPI.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import DocumentType


class DocumentSummary(BaseModel):
    """
    Resumo de um documento para listagem na API.

    Versão simplificada de StoredDocument sem o caminho original.
    """
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    filename: str
    mime_type: str
    document_type: DocumentType
    chunk_count: int
    created_at: datetime


class UploadResponse(BaseModel):
    """
    Resposta da API após upload de documentos.

    Contém a lista de documentos que foram processados e indexados.
    """
    documents: list[DocumentSummary]


class ChatRequest(BaseModel):
    """
    Payload de requisição para o endpoint de chat.

    Valida que a pergunta não está vazia e que top_k está
    dentro do intervalo permitido (1-20).
    """
    question: str = Field(min_length=1)
    document_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value: object) -> object:
        """
        Remove espaços em branco do início e fim da pergunta.

        Args:
            value: Valor bruto da pergunta

        Returns:
            Pergunta sem espaços extras
        """
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("document_id", mode="before")
    @classmethod
    def normalize_document_id(cls, value: object) -> str | None:
        """
        Normaliza o document_id, convertendo strings vazias em None.

        Args:
            value: Valor bruto do document_id

        Returns:
            document_id sanitizado ou None
        """
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return str(value)


class ChatSourceResponse(BaseModel):
    """
    Representação de uma fonte/citação na resposta da API.

    Inclui informações de localização e um trecho resumido do texto.
    """
    document_id: str
    filename: str
    page: int | None = None
    sheet: str | None = None
    chunk_index: int
    excerpt: str
    score: float


class ChatResponse(BaseModel):
    """
    Resposta completa da API para uma pergunta de chat.

    Contém a resposta gerada pelo LLM e as fontes usadas como contexto.
    """
    answer: str
    sources: list[ChatSourceResponse]

