"""
Roteador principal da API.

Agrupa todos os sub-roteadores da aplicação em um único router
que é incluído na aplicação FastAPI. Define os prefixos de caminho
para cada grupo de endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router

# Roteador principal que agrupa todos os endpoints
router = APIRouter()

# Health check sem prefixo (acessível em /health)
router.include_router(health_router)

# Endpoints de documentos em /api/documents
router.include_router(documents_router, prefix="/api")

# Endpoints de chat em /api/chat
router.include_router(chat_router, prefix="/api")

