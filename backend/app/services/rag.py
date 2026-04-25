from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.core.storage import DocumentStorage
from app.models import ChatResult, IncomingFile, StoredDocument, VectorMatch
from app.services.chunking import ChunkingService
from app.services.embeddings import EmbeddingService
from app.services.file_loader import FileLoaderService
from app.services.llm import OllamaClient, OllamaUnavailableError
from app.services.vector_store import VectorStore

_DEFAULT_MIME_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class RAGService:
    def __init__(
        self,
        settings: Settings | None = None,
        storage: DocumentStorage | None = None,
        file_loader: FileLoaderService | None = None,
        chunking_service: ChunkingService | None = None,
        embeddings_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
        llm_client: OllamaClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.storage = storage or DocumentStorage(self.settings)
        self.file_loader = file_loader or FileLoaderService()
        self.chunking_service = chunking_service or ChunkingService(
            max_chunk_chars=self.settings.chunk_size_chars,
            sentence_overlap=self.settings.chunk_overlap_sentences,
        )
        self.embeddings_service = embeddings_service or EmbeddingService(self.settings.embedding_model)
        self.vector_store = vector_store or VectorStore(
            persist_directory=self.settings.chroma_dir,
            collection_name=self.settings.chroma_collection_name,
        )
        self.llm_client = llm_client or OllamaClient(
            base_url=self.settings.ollama_base_url,
            model=self.settings.ollama_model,
            timeout_seconds=self.settings.ollama_timeout_seconds,
        )

    def list_documents(self) -> list[StoredDocument]:
        return self.storage.list_documents()

    def ingest_files(self, files: Sequence[IncomingFile]) -> list[StoredDocument]:
        if not files:
            raise ValueError("At least one file is required for ingestion.")

        ingested_documents: list[StoredDocument] = []
        for incoming_file in files:
            if not incoming_file.filename.strip():
                raise ValueError("Each uploaded file must have a filename.")
            if not incoming_file.content:
                raise ValueError(f"File '{incoming_file.filename}' is empty.")

            document_type = self.file_loader.detect_document_type(
                incoming_file.filename,
                incoming_file.content_type,
            )
            document_id = uuid4().hex
            mime_type = self._normalize_mime_type(
                incoming_file.content_type,
                incoming_file.filename,
            )
            original_path = self.storage.save_original_file(
                document_id=document_id,
                filename=incoming_file.filename,
                content=incoming_file.content,
            )
            sections = self.file_loader.load_sections(
                file_path=original_path,
                document_id=document_id,
                filename=incoming_file.filename,
                mime_type=mime_type,
            )
            chunks = self.chunking_service.chunk_sections(sections)
            if not chunks:
                raise ValueError(f"No indexable chunks were generated for '{incoming_file.filename}'.")

            embeddings = self.embeddings_service.encode([chunk.text for chunk in chunks])
            self.vector_store.add_chunks(chunks, embeddings)

            stored_document = StoredDocument(
                id=document_id,
                filename=incoming_file.filename,
                mime_type=mime_type,
                document_type=document_type,
                chunk_count=len(chunks),
                created_at=datetime.now(timezone.utc),
                original_path=str(original_path),
            )
            self.storage.upsert_document(stored_document)
            ingested_documents.append(stored_document)

        return ingested_documents

    def answer_question(
        self,
        question: str,
        document_id: str | None = None,
        top_k: int = 5,
    ) -> ChatResult:
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        query_embedding = self.embeddings_service.embed_query(cleaned_question)
        matches = self.vector_store.query(query_embedding, top_k, document_id=document_id)

        if not matches:
            return ChatResult(
                answer=self._build_fallback_answer(cleaned_question, matches, document_id=document_id),
                sources=[],
            )

        prompt = self._build_prompt(cleaned_question, matches)
        try:
            answer = self.llm_client.generate(prompt)
        except OllamaUnavailableError:
            answer = self._build_fallback_answer(cleaned_question, matches, document_id=document_id)

        return ChatResult(answer=answer, sources=matches)

    def _build_prompt(self, question: str, matches: Sequence[VectorMatch]) -> str:
        context_blocks = []
        for index, match in enumerate(matches, start=1):
            context_blocks.append(
                "\n".join(
                    [
                        f"Source {index}:",
                        f"Document: {match.filename}",
                        self._format_location(match),
                        f"Chunk index: {match.chunk_index}",
                        f"Score: {match.score:.3f}",
                        "Excerpt:",
                        self._truncate_text(match.text, 1200),
                    ]
                ).strip()
            )

        context = "\n\n".join(context_blocks)
        return "\n".join(
            [
                "You are a careful document question-answering assistant.",
                "Use only the provided context to answer the question.",
                "If the context does not contain the answer, say that the answer could not be determined from the indexed documents.",
                "Respond in the same language as the question when possible.",
                "Keep the answer concise but helpful.",
                "",
                f"Question: {question}",
                "",
                "Context:",
                context,
            ]
        )

    def _build_fallback_answer(
        self,
        question: str,
        matches: Sequence[VectorMatch],
        document_id: str | None = None,
    ) -> str:
        if not matches:
            scope_message = "the indexed documents" if document_id is None else f"document '{document_id}'"
            return (
                "I couldn't reach Ollama, and no relevant chunks were retrieved from "
                f"{scope_message}. So I can't answer the question confidently yet."
            )

        lines = [
            "I couldn't reach Ollama, so this answer is built deterministically from the retrieved document chunks.",
            f"Question: {question}",
            "",
            "Most relevant source excerpts:",
        ]
        for index, match in enumerate(matches, start=1):
            lines.append(
                f"{index}. {match.filename} ({self._format_location(match)}, chunk {match.chunk_index}, score {match.score:.3f}): "
                f"{self._truncate_text(match.text, 260)}"
            )
        lines.append("")
        lines.append("Answer: The retrieved passages above are the best available evidence for the question.")
        return "\n".join(lines)

    def _format_location(self, match: VectorMatch) -> str:
        parts: list[str] = []
        if match.page is not None:
            parts.append(f"page {match.page}")
        if match.sheet:
            parts.append(f"sheet {match.sheet}")
        if match.row_start is not None and match.row_end is not None:
            parts.append(f"rows {match.row_start}-{match.row_end}")
        return ", ".join(parts) if parts else "document chunk"

    def _truncate_text(self, text: str, limit: int) -> str:
        collapsed = " ".join(text.split())
        if len(collapsed) <= limit:
            return collapsed
        return f"{collapsed[: limit - 1].rstrip()}…"

    def _normalize_mime_type(self, mime_type: str | None, filename: str) -> str:
        if mime_type and mime_type != "application/octet-stream":
            return mime_type
        return _DEFAULT_MIME_TYPES.get(self._extension(filename), "application/octet-stream")

    def _extension(self, filename: str) -> str:
        from pathlib import Path

        return Path(filename).suffix.lower()


def create_rag_service(settings: Settings | None = None) -> RAGService:
    return RAGService(settings=settings or get_settings())