from __future__ import annotations

from fastapi import Request

from app.services.rag import RAGService


def get_rag_service(request: Request) -> RAGService:
    service = getattr(request.app.state, "rag_service", None)
    if not isinstance(service, RAGService):
        raise RuntimeError("RAG service has not been initialized.")
    return service