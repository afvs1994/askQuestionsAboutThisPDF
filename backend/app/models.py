"""
Modelos de dados Pydantic para a aplicação RAG.

Define as estruturas de dados usadas em todo o pipeline:
- Documentos armazenados e seus metadados
- Seções e chunks de texto extraídos
- Resultados de busca vetorial
- Respostas do chat

Todos os modelos usam ConfigDict(extra="ignore") para serem
resilientes a campos adicionais não esperados.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DocumentType(str, Enum):
    """
    Tipos de documentos suportados pelo sistema.

    Cada valor corresponde a uma estratégia de extração de texto
    diferente no pipeline de ingestão.
    """
    pdf = "pdf"
    docx = "docx"
    xlsx = "xlsx"
    unknown = "unknown"


class StoredDocument(BaseModel):
    """
    Representação de um documento persistido no registro.

    Contém metadados sobre o arquivo original e estatísticas
    do processamento (número de chunks gerados).
    """
    model_config = ConfigDict(extra="ignore")

    id: str
    filename: str
    mime_type: str
    document_type: DocumentType
    chunk_count: int
    created_at: datetime
    original_path: str


class IncomingFile(BaseModel):
    """
    Arquivo recebido via upload antes do processamento.

    Armazena o conteúdo binário e metadados do arquivo enviado.
    """
    model_config = ConfigDict(extra="ignore")

    filename: str
    content: bytes
    content_type: str | None = None


class DocumentSection(BaseModel):
    """
    Seção de texto extraída de um documento.

    Uma seção representa uma unidade lógica do documento
    (página de PDF, planilha de Excel, etc.) antes do chunking.
    """
    model_config = ConfigDict(extra="ignore")

    document_id: str
    filename: str
    mime_type: str
    document_type: DocumentType
    text: str
    section_index: int
    page: int | None = None
    sheet: str | None = None
    row_start: int | None = None
    row_end: int | None = None


class DocumentChunk(BaseModel):
    """
    Fragmento de texto resultante do processo de chunking.

    Cada chunk é a unidade mínima indexada no banco de vetores
    e recuperada durante a busca semântica.
    """
    model_config = ConfigDict(extra="ignore")

    document_id: str
    filename: str
    mime_type: str
    document_type: DocumentType
    text: str
    chunk_index: int
    section_index: int
    page: int | None = None
    sheet: str | None = None
    row_start: int | None = None
    row_end: int | None = None


class VectorMatch(BaseModel):
    """
    Resultado de uma busca por similaridade no banco de vetores.

    Representa um chunk que foi considerado semanticamente relevante
    para a pergunta do usuário, incluindo o score de similaridade.
    """
    model_config = ConfigDict(extra="ignore")

    document_id: str
    filename: str
    mime_type: str
    document_type: DocumentType
    text: str
    chunk_index: int
    score: float
    page: int | None = None
    sheet: str | None = None
    row_start: int | None = None
    row_end: int | None = None


class ChatResult(BaseModel):
    """
    Resultado completo de uma interação de chat.

    Contém a resposta textual gerada pelo LLM e a lista de fontes
    (chunks recuperados) que foram usadas como contexto.
    """
    model_config = ConfigDict(extra="ignore")

    answer: str
    sources: list[VectorMatch]

