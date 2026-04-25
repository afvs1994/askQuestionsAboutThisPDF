from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.dependencies import get_rag_service
from app.models import IncomingFile, StoredDocument
from app.schemas import DocumentSummary, UploadResponse
from app.services.rag import RAGService

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_document_summary(document: StoredDocument) -> DocumentSummary:
    return DocumentSummary.model_validate(document)


@router.get("", response_model=list[DocumentSummary])
async def list_documents(service: RAGService = Depends(get_rag_service)) -> list[DocumentSummary]:
    documents = await asyncio.to_thread(service.list_documents)
    return [_to_document_summary(document) for document in documents]


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(..., description="One or more files to ingest"),
    service: RAGService = Depends(get_rag_service),
) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required.")

    incoming_files: list[IncomingFile] = []
    for upload_file in files:
        if not upload_file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Every file must have a filename.")
        content = await upload_file.read()
        incoming_files.append(
            IncomingFile(
                filename=upload_file.filename,
                content=content,
                content_type=upload_file.content_type,
            )
        )

    try:
        documents = await asyncio.to_thread(service.ingest_files, incoming_files)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return UploadResponse(documents=[_to_document_summary(document) for document in documents])