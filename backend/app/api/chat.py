from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_rag_service
from app.models import ChatResult, VectorMatch
from app.schemas import ChatRequest, ChatResponse, ChatSourceResponse
from app.services.rag import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])


def _build_excerpt(text: str, limit: int = 280) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 1].rstrip()}…"


def _to_source_response(source: VectorMatch) -> ChatSourceResponse:
    return ChatSourceResponse(
        document_id=source.document_id,
        filename=source.filename,
        page=source.page,
        sheet=source.sheet,
        chunk_index=source.chunk_index,
        excerpt=_build_excerpt(source.text),
        score=source.score,
    )


def _to_chat_response(result: ChatResult) -> ChatResponse:
    return ChatResponse(
        answer=result.answer,
        sources=[_to_source_response(source) for source in result.sources],
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    try:
        result = await asyncio.to_thread(
            service.answer_question,
            request.question,
            request.document_id,
            request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return _to_chat_response(result)