"""
Endpoints para gestão de documentos.

Fornece operações CRD (Create, Read, Delete implícito via sobrescrita)
para documentos no sistema RAG:
- Listar documentos indexados
- Fazer upload de novos documentos para ingestão
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.dependencies import get_rag_service
from app.models import IncomingFile, StoredDocument
from app.schemas import DocumentSummary, UploadResponse
from app.services.rag import RAGService

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_document_summary(document: StoredDocument) -> DocumentSummary:
    """
    Converte um StoredDocument para o schema de resumo da API.

    Args:
        document: Documento do domínio

    Returns:
        DocumentSummary para serialização JSON
    """
    return DocumentSummary.model_validate(document)


@router.get("", response_model=list[DocumentSummary])
async def list_documents(service: RAGService = Depends(get_rag_service)) -> list[DocumentSummary]:
    """
    Lista todos os documentos indexados no sistema.

    Os documentos são retornados ordenados por data de criação
    decrescente (mais recentes primeiro).

    Args:
        service: Serviço RAG injetado via dependência

    Returns:
        Lista de resumos de documentos
    """
    documents = await asyncio.to_thread(service.list_documents)
    return [_to_document_summary(document) for document in documents]


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(..., description="One or more files to ingest"),
    service: RAGService = Depends(get_rag_service),
) -> UploadResponse:
    """
    Faz upload de um ou mais documentos para ingestão no sistema RAG.

    Os arquivos são processados de forma síncrona (em thread separada)
    para evitar bloqueio do event loop do asyncio. Cada arquivo passa
    por extração de texto, chunking, embedding e indexação vetorial.

    Args:
        files: Lista de arquivos para upload
        service: Serviço RAG injetado via dependência

    Returns:
        Resposta com os documentos processados e indexados

    Raises:
        HTTPException: 400 se nenhum arquivo for enviado ou se houver erro de validação
        HTTPException: 503 se houver erro no processamento do serviço
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pelo menos um arquivo é necessário.")

    incoming_files: list[IncomingFile] = []
    for upload_file in files:
        if not upload_file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cada arquivo deve ter um nome.")

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


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    service: RAGService = Depends(get_rag_service),
) -> dict[str, bool]:
    """
    Remove permanentemente um documento do sistema RAG.

    Deleta o documento do registro de metadados, remove o arquivo original
    do filesystem e elimina todos os chunks vetoriais associados no ChromaDB.
    A operação é irreversível.

    Args:
        document_id: UUID do documento a ser removido
        service: Serviço RAG injetado via dependência

    Returns:
        Dicionário com confirmação de remoção: {"deleted": True}

    Raises:
        HTTPException: 404 se o documento não for encontrado
        HTTPException: 503 se houver erro no serviço de deleção
    """
    try:
        deleted = await asyncio.to_thread(service.delete_document, document_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao remover documento: {exc}",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado.",
        )

    return {"deleted": True}


