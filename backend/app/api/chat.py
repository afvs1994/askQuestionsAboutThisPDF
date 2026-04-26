"""
Endpoint de chat do assistente RAG.

Recebe perguntas dos usuários, recupera contexto relevante dos documentos
indexados via busca semântica, e gera respostas usando um LLM.
Todas as respostas incluem citações das fontes usadas.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_rag_service
from app.models import ChatResult, VectorMatch
from app.schemas import ChatRequest, ChatResponse, ChatSourceResponse
from app.services.rag import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])


# Limite de caracteres para o trecho exibido na citação
_EXCERPT_LIMIT = 280


def _build_excerpt(text: str, limit: int = _EXCERPT_LIMIT) -> str:
    """
    Constrói um trecho resumido do texto original.

    Remove quebras de linha excessivas e trunca se necessário,
    adicionando reticências no final.

    Args:
        text: Texto original do chunk
        limit: Número máximo de caracteres no trecho

    Returns:
        Trecho resumido e sanitizado
    """
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 1].rstrip()}…"


def _to_source_response(source: VectorMatch) -> ChatSourceResponse:
    """
    Converte um VectorMatch para o schema de resposta da API.

    Args:
        source: Resultado de busca vetorial

    Returns:
        ChatSourceResponse com trecho resumido
    """
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
    """
    Converte um ChatResult para o schema de resposta da API.

    Args:
        result: Resultado do processamento RAG

    Returns:
        ChatResponse serializável
    """
    return ChatResponse(
        answer=result.answer,
        sources=[_to_source_response(source) for source in result.sources],
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    """
    Processa uma pergunta do usuário usando o pipeline RAG.

    Fluxo:
    1. Recebe a pergunta e parâmetros opcionais (document_id, top_k)
    2. Busca os chunks mais similares no banco de vetores
    3. Envia pergunta + contexto ao LLM via Ollama
    4. Retorna a resposta com citações das fontes

    Args:
        request: Pergunta e parâmetros de busca
        service: Serviço RAG injetado via dependência

    Returns:
        Resposta do assistente com fontes citadas

    Raises:
        HTTPException: 400 para erros de validação
        HTTPException: 503 se o serviço LLM estiver indisponível
    """
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

