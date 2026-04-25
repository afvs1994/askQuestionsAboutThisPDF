from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import DocumentType


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    filename: str
    mime_type: str
    document_type: DocumentType
    chunk_count: int
    created_at: datetime


class UploadResponse(BaseModel):
    documents: list[DocumentSummary]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    document_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("document_id", mode="before")
    @classmethod
    def normalize_document_id(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return str(value)


class ChatSourceResponse(BaseModel):
    document_id: str
    filename: str
    page: int | None = None
    sheet: str | None = None
    chunk_index: int
    excerpt: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceResponse]