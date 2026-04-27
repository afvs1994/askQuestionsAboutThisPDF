"""
Geração de embeddings semânticos via sentence-transformers.

Converte textos em vetores numéricos densos que capturam o significado
semântico, permitindo busca por similaridade no banco de vetores.

Usa o modelo multilingual para suportar textos em português e inglês.
O modelo é carregado sob demanda e cacheado para reutilização.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings


@lru_cache(maxsize=1)
def _get_embedding_model(model_name: str):
    """
    Carrega e cacheia o modelo de embeddings.

    O cache via lru_cache garante que o modelo seja carregado
    apenas uma vez, economizando memória e tempo de inicialização.

    Args:
        model_name: Nome do modelo no HuggingFace Hub

    Returns:
        Modelo sentence-transformers carregado
    """
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


def get_embeddings(texts: list[str], settings: Settings) -> list[list[float]]:
    """
    Gera embeddings para uma lista de textos.

    Args:
        texts: Lista de strings para vetorizar
        settings: Configurações com o nome do modelo de embedding

    Returns:
        Lista de vetores (cada vetor é uma lista de floats)

    Raises:
        RuntimeError: Se houver erro no carregamento do modelo ou na geração
    """
    if not texts:
        return []

    try:
        model = _get_embedding_model(settings.embedding_model)
        embeddings = model.encode(texts)
        # Converte arrays numpy para listas Python nativas
        return [embedding.tolist() for embedding in embeddings]
    except Exception as exc:
        raise RuntimeError(f"Falha em gerar os embarcados: {exc}") from exc

