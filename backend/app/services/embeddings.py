from __future__ import annotations

from typing import Sequence

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingModelUnavailableError(RuntimeError):
    pass


class EmbeddingService:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model: object | None = None

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load_model()
        encode = getattr(model, "encode")
        try:
            embedding_array = encode(
                list(texts),
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            raise EmbeddingModelUnavailableError(
                f"Unable to generate embeddings with model '{self.model_name}'."
            ) from exc

        if hasattr(embedding_array, "tolist"):
            raw_embeddings = embedding_array.tolist()
        else:
            raw_embeddings = list(embedding_array)
        return [[float(value) for value in embedding] for embedding in raw_embeddings]

    def embed_query(self, text: str) -> list[float]:
        embeddings = self.encode([text])
        return embeddings[0] if embeddings else []

    def _load_model(self) -> object:
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingModelUnavailableError(
                "sentence-transformers is not installed. Install the backend requirements to enable embeddings."
            ) from exc

        try:
            self._model = SentenceTransformer(self.model_name)
        except Exception as exc:
            raise EmbeddingModelUnavailableError(
                f"Unable to load embedding model '{self.model_name}'. Verify that the model name is correct and the environment has access to it."
            ) from exc

        return self._model