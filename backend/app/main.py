"""
Ponto de entrada da aplicação FastAPI.

Responsável por criar e configurar a instância da aplicação FastAPI,
incluindo:
- Ciclo de vida (lifespan) para inicialização de serviços
- Configuração de CORS para comunicação com o frontend
- Inclusão das rotas da API
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.config import get_settings
from app.services.rag import create_rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciador de ciclo de vida da aplicação.

    Executado na inicialização (before yield) e no encerramento (after yield).
    No startup, carrega as configurações e inicializa o serviço RAG,
    armazenando ambos no estado da aplicação para injeção de dependências.

    Args:
        app: Instância da aplicação FastAPI

    Yields:
        Controle para o runtime do FastAPI
    """
    settings = get_settings()
    app.state.settings = settings
    app.state.rag_service = create_rag_service(settings)
    yield


def create_app() -> FastAPI:
    """
    Factory que cria e configura a aplicação FastAPI.

    Configurações aplicadas:
    - Título da API a partir das settings
    - Middleware CORS para permitir requisições do frontend
    - Inclusão do roteador principal com todos os endpoints

    Returns:
        Instância configurada do FastAPI
    """
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # Configuração de CORS para permitir comunicação com o frontend React
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


# Instância global da aplicação, usada pelo servidor ASGI
app = create_app()

