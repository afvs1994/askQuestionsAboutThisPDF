from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence, cast

from app.models import DocumentChunk, DocumentType, VectorMatch


class ChromaCollectionProtocol(Protocol):
    def upsert(
        self,
        *,
        ids: Sequence[str],
        documents: Sequence[str],
        metadatas: Sequence[dict[str, object]],
        embeddings: Sequence[Sequence[float]],
    ) -> None: ...

    def query(
        self,
        *,
        query_embeddings: Sequence[Sequence[float]],
        n_results: int,
        where: dict[str, object] | None = None,
        include: Sequence[str] | None = None,
    ) -> dict[str, list[list[object]]]: ...

    def count(self) -> int: ...


class VectorStore:
    def __init__(self, persist_directory: Path, collection_name: str) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client: object | None = None
        self._collection: ChromaCollectionProtocol | None = None
        self.persist_directory.mkdir(parents=True, exist_ok=True)

    def add_chunks(self, chunks: Sequence[DocumentChunk], embeddings: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("The number of chunks must match the number of embeddings.")
        if not chunks:
            return

        collection = self._get_collection()
        ids = [self._chunk_id(chunk) for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [self._metadata_from_chunk(chunk) for chunk in chunks]
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def query(
        self,
        query_embedding: Sequence[float],
        top_k: int,
        document_id: str | None = None,
    ) -> list[VectorMatch]:
        collection = self._get_collection()
        if collection.count() == 0:
            return []

        where = {"document_id": document_id} if document_id else None
        result = collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        documents = self._extract_nested(result, "documents")
        metadatas = self._extract_nested(result, "metadatas")
        distances = self._extract_nested(result, "distances")

        matches: list[VectorMatch] = []
        for document_text, metadata_value, distance_value in zip(documents, metadatas, distances):
            metadata = metadata_value if isinstance(metadata_value, dict) else {}
            try:
                distance = float(distance_value)
            except (TypeError, ValueError):
                distance = 1.0
            score = max(0.0, 1.0 - distance)
            matches.append(
                VectorMatch(
                    document_id=str(metadata.get("document_id", "")),
                    filename=str(metadata.get("filename", "")),
                    mime_type=str(metadata.get("mime_type", "")),
                    document_type=self._parse_document_type(metadata.get("document_type")),
                    text=str(document_text or ""),
                    chunk_index=self._parse_int(metadata.get("chunk_index"), default=0),
                    score=score,
                    page=self._optional_int(metadata.get("page")),
                    sheet=self._optional_str(metadata.get("sheet")),
                    row_start=self._optional_int(metadata.get("row_start")),
                    row_end=self._optional_int(metadata.get("row_end")),
                )
            )

        return matches

    def _get_collection(self) -> ChromaCollectionProtocol:
        if self._collection is not None:
            return self._collection

        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb is required to use the vector store.") from exc

        if self._client is None:
            self._client = chromadb.PersistentClient(path=str(self.persist_directory))

        client = cast(object, self._client)
        self._collection = client.get_or_create_collection(  # type: ignore[attr-defined]
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    def _chunk_id(self, chunk: DocumentChunk) -> str:
        return f"{chunk.document_id}:{chunk.chunk_index:06d}"

    def _metadata_from_chunk(self, chunk: DocumentChunk) -> dict[str, object]:
        return {
            "document_id": chunk.document_id,
            "filename": chunk.filename,
            "mime_type": chunk.mime_type,
            "document_type": chunk.document_type.value,
            "chunk_index": chunk.chunk_index,
            "section_index": chunk.section_index,
            "page": chunk.page if chunk.page is not None else -1,
            "sheet": chunk.sheet or "",
            "row_start": chunk.row_start if chunk.row_start is not None else -1,
            "row_end": chunk.row_end if chunk.row_end is not None else -1,
        }

    def _extract_nested(self, payload: dict[str, list[list[object]]], key: str) -> list[object]:
        value = payload.get(key, [])
        if not value:
            return []
        first = value[0]
        if isinstance(first, list):
            return list(first)
        return list(value)

    def _optional_int(self, value: object) -> int | None:
        try:
            integer = int(value)
        except (TypeError, ValueError):
            return None
        return integer if integer >= 0 else None

    def _optional_str(self, value: object) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return None

    def _parse_int(self, value: object, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _parse_document_type(self, value: object) -> DocumentType:
        if isinstance(value, DocumentType):
            return value
        if isinstance(value, str):
            try:
                return DocumentType(value)
            except ValueError:
                return DocumentType.unknown
        return DocumentType.unknown