"""
Comunicação com modelos de linguagem via API Ollama.

Fornece uma interface simplificada para enviar prompts ao LLM
local (via Ollama), com tratamento de timeout e parsing da resposta.

O Ollama permite rodar modelos como Llama 3 localmente,
garantindo privacidade dos dados corporativos.
"""
from __future__ import annotations

import json

import httpx

from app.core.config import Settings


def generate_answer(prompt: str, settings: Settings) -> str:
    """
    Envia um prompt ao LLM via Ollama e retorna a resposta textual.

    Args:
        prompt: Texto completo do prompt (sistema + contexto + pergunta)
        settings: Configurações com URL do Ollama, nome do modelo e timeout

    Returns:
        Resposta textual gerada pelo modelo

    Raises:
        RuntimeError: Se o Ollama estiver indisponível ou retornar erro
    """
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=settings.ollama_timeout_seconds) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.ConnectError as exc:
        raise RuntimeError(
            f"Cannot connect to Ollama at {settings.ollama_base_url}. "
            "Make sure Ollama is running and the model is pulled."
        ) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            f"Ollama request timed out after {settings.ollama_timeout_seconds}s."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    # Extrai a resposta do campo "response" do formato Ollama
    answer = data.get("response", "").strip()
    if not answer:
        raise RuntimeError("Ollama returned an empty response.")

    return answer


def build_rag_prompt(question: str, context_chunks: list[str]) -> str:
    """
    Constrói o prompt completo para o LLM no formato RAG.

    O prompt inclui:
    1. Instruções de sistema (responder apenas com base no contexto)
    2. Contexto recuperado dos documentos
    3. Pergunta do usuário

    Args:
        question: Pergunta do usuário
        context_chunks: Trechos recuperados do banco de vetores

    Returns:
        Prompt formatado pronto para envio ao LLM
    """
    context_text = "\n\n---\n\n".join(context_chunks)

    prompt = (
        "You are a helpful technical assistant. Answer the user's question "
        "based ONLY on the provided context below. If the context does not "
        "contain enough information to answer, say so clearly. "
        "Do not make up information.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    return prompt

