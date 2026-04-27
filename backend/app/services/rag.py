"""
Orquestrador do pipeline RAG (Retrieval-Augmented Generation).

Coordena todos os serviços do pipeline:
1. Ingestão: carrega arquivo → extrai texto → chunking → embedding → indexa
2. Resposta: recebe pergunta → embedding → busca vetorial → prompt → LLM

É o ponto central da aplicação, consumido pelos endpoints da API.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import Settings
from app.core.storage import DocumentStorage
from app.models import ChatResult, DocumentChunk, DocumentType, IncomingFile, StoredDocument, VectorMatch
from app.services.chunking import chunk_sections
from app.services.embeddings import get_embeddings
from app.services.file_loader import load_file_sections
from app.services.llm import build_rag_prompt, generate_answer
from app.services.vector_store import VectorStore


class RAGService:
    """
    Serviço principal que orquestra o pipeline RAG completo.

    Mantém referências ao storage de documentos e ao vector store,
    coordenando o fluxo de ingestão e consulta.
    """

    def __init__(self, settings: Settings, storage: DocumentStorage, vector_store: VectorStore) -> None:
        """
        Inicializa o serviço RAG com suas dependências.

        Args:
            settings: Configurações da aplicação
            storage: Gerenciador de persistência de documentos
            vector_store: Banco de vetores para busca semântica
        """
        self.settings = settings
        self.storage = storage
        self.vector_store = vector_store

    def list_documents(self) -> list[StoredDocument]:
        """
        Lista todos os documentos indexados.

        Returns:
            Lista de documentos ordenados por data decrescente
        """
        return self.storage.list_documents()

    def ingest_files(self, incoming_files: list[IncomingFile]) -> list[StoredDocument]:
        """
        Processa uma lista de arquivos pelo pipeline completo de ingestão.

        Fluxo por arquivo:
        1. Detecta tipo e extrai texto (file_loader)
        2. Divide em chunks semânticos (chunking)
        3. Gera embeddings (embeddings)
        4. Indexa no ChromaDB (vector_store)
        5. Registra metadados no JSON (storage)

        Args:
            incoming_files: Lista de arquivos recebidos via upload

        Returns:
            Lista de documentos processados e indexados

        Raises:
            ValueError: Se algum arquivo tiver formato não suportado
            RuntimeError: Se houver erro no processamento
        """
        stored_documents: list[StoredDocument] = []

        for incoming_file in incoming_files:
            # 1. Extrai seções de texto do arquivo
            sections = load_file_sections(incoming_file)
            if not sections:
                raise ValueError(f"Nenhum texto pôde ser extraído de {incoming_file.filename}")

            document_id = sections[0].document_id
            document_type = sections[0].document_type

            # 2. Divide em chunks
            chunks = chunk_sections(sections, self.settings)
            if not chunks:
                raise ValueError(f"Não foi possível criar nenhum fragmento a partir de {incoming_file.filename}")

            # 3. Gera embeddings para todos os chunks
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = get_embeddings(chunk_texts, self.settings)

            # 4. Indexa no vector store
            self.vector_store.add_chunks(chunks, embeddings)

            # 5. Salva o arquivo original
            original_path = self.storage.save_original_file(
                document_id, incoming_file.filename, incoming_file.content
            )

            # 6. Registra metadados
            stored_document = StoredDocument(
                id=document_id,
                filename=incoming_file.filename,
                mime_type=incoming_file.content_type or "application/octet-stream",
                document_type=document_type,
                chunk_count=len(chunks),
                created_at=datetime.now(timezone.utc),
                original_path=str(original_path),
            )
            self.storage.upsert_document(stored_document)
            stored_documents.append(stored_document)

        return stored_documents

    def answer_question(
        self,
        question: str,
        document_id: str | None = None,
        top_k: int | None = None,
    ) -> ChatResult:
        """
        Responde uma pergunta usando o pipeline RAG.

        Fluxo:
        1. Gera embedding da pergunta
        2. Busca chunks similares no vector store
        3. Constrói prompt com contexto recuperado
        4. Envia ao LLM e retorna resposta + fontes

        Args:
            question: Pergunta do usuário
            document_id: Se fornecido, limita busca a este documento
            top_k: Número de chunks a recuperar (usa padrão se None)

        Returns:
            Resultado com resposta do LLM e fontes citadas

        Raises:
            ValueError: Se a pergunta for inválida
            RuntimeError: Se houver erro na comunicação com LLM ou vector store
        """
        if not question or not question.strip():
            raise ValueError("A pergunta não pode ser vazia.")

        k = top_k if top_k is not None else self.settings.top_k_default

        # 1. Embedding da pergunta
        query_embeddings = get_embeddings([question.strip()], self.settings)
        if not query_embeddings:
            raise RuntimeError("Falha ao gerar embarcado de consulta.")
        query_embedding = query_embeddings[0]

        # 2. Busca vetorial
        matches = self.vector_store.search(query_embedding, k, document_id)
        if not matches:
            return ChatResult(
                answer="Não consegui encontrar informações relevantes nos documentos fornecidos para responder à sua pergunta.",
                sources=[],
            )

        # 3. Constrói prompt com contexto
        context_chunks = [match.text for match in matches]
        prompt = build_rag_prompt(question, context_chunks)

        # 4. Gera resposta via LLM
        answer = generate_answer(prompt, self.settings)

        return ChatResult(answer=answer, sources=matches)

    def delete_document(self, document_id: str) -> bool:
        """
        Remove permanentemente um documento do sistema RAG.

        Executa a remoção em duas etapas:
        1. Deleta todos os chunks vetoriais associados ao documento no ChromaDB
        2. Remove o registro de metadados e os arquivos originais do storage

        Args:
            document_id: UUID do documento a ser removido

        Returns:
            True se o documento existia e foi removido com sucesso, False caso contrário
        """
        # Verifica se o documento existe antes de tentar deletar
        document = self.storage.get_document(document_id)
        if document is None:
            return False

        # 1. Remove os embeddings do vector store (ChromaDB)
        # Esta operação é idempotente: se os chunks já não existirem, retorna 0
        self.vector_store.delete_by_document_id(document_id)

        # 2. Remove o registro do documento e os arquivos originais do filesystem
        return self.storage.delete_document(document_id)


def create_rag_service(settings: Settings) -> RAGService:
    """
    Factory que cria uma instância completa do RAGService.

    Inicializa todas as dependências (storage e vector store)
    com base nas configurações fornecidas.

    Args:
        settings: Configurações da aplicação

    Returns:
        Instância pronta para uso de RAGService
    """
    storage = DocumentStorage(settings)
    vector_store = VectorStore(settings)
    return RAGService(settings, storage, vector_store)

