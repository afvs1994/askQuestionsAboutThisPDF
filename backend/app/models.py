from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DocumentType(str, Enum):
    pdf = "pdf"
    docx = "docx"
    xlsx = "xlsx"
    unknown = "unknown"


class StoredDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    filename: str
    mime_type: str
    document_type: DocumentType
    chunk_count: int
    created_at: datetime
    original_path: str


class IncomingFile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: str
    content: bytes
    content_type: str | None = None


class DocumentSection(BaseModel):
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
    model_config = ConfigDict(extra="ignore")

    answer: str
    sources: list[VectorMatch]