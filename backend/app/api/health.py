"""
Endpoint de verificação de saúde do serviço.

Fornece um endpoint simples para health checks de load balancers
e ferramentas de monitoramento verificarem se o serviço está respondendo.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """
    Verifica se o serviço está operacional.

    Returns:
        Dicionário com status "ok" indicando que o serviço está saudável
    """
    return {"status": "ok"}

