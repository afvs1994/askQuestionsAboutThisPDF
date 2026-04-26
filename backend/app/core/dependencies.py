"""
Injeção de dependências para os endpoints da API.

Fornece funções que extraem serviços inicializados do estado da
aplicação FastAPI, permitindo que os endpoints recebam as dependências
prontas para uso sem acoplamento direto com a inicialização.
"""
from __future__ import annotations

from fastapi import Request

from app.services.rag import RAGService


def get_rag_service(request: Request) -> RAGService:
    """
    Extrai o serviço RAG do estado da aplicação.

    Usado como dependência nos endpoints que precisam interagir
    com o pipeline de ingestão e resposta do RAG.

    Args:
        request: Objeto Request do FastAPI com acesso ao app.state

    Returns:
        Instância inicializada de RAGService

    Raises:
        RuntimeError: Se o serviço não foi inicializado no lifespan
    """
    service = getattr(request.app.state, "rag_service", None)
    if not isinstance(service, RAGService):
        raise RuntimeError("RAG service has not been initialized.")
    return service

