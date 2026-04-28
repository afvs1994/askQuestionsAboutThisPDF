"""
Armazenamento e busca por similaridade via ChromaDB.

Implementa a camada de Vector Store do pipeline RAG:
- Inicialização do cliente ChromaDB persistente
- Criação/atualização de coleções
- Inserção de documentos com embeddings e metadados
- Busca por similaridade com filtro opcional por documento
"""
from __future__ import annotations

from app.core.config import Settings
from app.models import DocumentChunk, VectorMatch


class VectorStore:
    """
    Wrapper thread-safe (single-threaded usage) sobre o ChromaDB.

    Gerencia uma coleção nomeada onde cada entrada contém:
    - ID único do chunk
    - Vetor de embedding
    - Documento original (texto)
    - Metadados estruturados para filtragem e citação
    """

    def __init__(self, settings: Settings) -> None:
        """
        Inicializa o VectorStore com as configurações da aplicação.

        Args:
            settings: Configurações com caminho do ChromaDB e nome da coleção
        """
        self.settings = settings
        self._client = None
        self._collection = None

    def _get_client(self):
        """
        Lazy-loading do cliente ChromaDB.

        O cliente só é criado na primeira operação, evitando
        inicialização custosa durante a importação do módulo.

        Returns:
            Cliente ChromaDB persistente
        """
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=str(self.settings.chroma_dir))
        return self._client

    def _get_collection(self):
        """
        Lazy-loading da coleção ChromaDB.

        Cria a coleção se não existir, ou recupera a existente.

        Returns:
            Coleção ChromaDB para operações de CRUD e busca
        """
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> int:
        """
        Adiciona chunks e seus embeddings à coleção vetorial.

        Args:
            chunks: Lista de chunks com metadados
            embeddings: Lista de vetores correspondentes

        Returns:
            Número de chunks inseridos

        Raises:
            ValueError: Se as listas tiverem comprimentos diferentes
            RuntimeError: Se houver erro na comunicação com o ChromaDB
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have the same length.")

        if not chunks:
            return 0

        collection = self._get_collection()

        ids = [f"{chunk.document_id}_{chunk.section_index}_{chunk.chunk_index}" for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            metadata: dict[str, str | int | float | bool] = {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "mime_type": chunk.mime_type,
                "document_type": chunk.document_type.value,
                "chunk_index": chunk.chunk_index,
                "section_index": chunk.section_index,
            }
            # Adiciona campos opcionais apenas quando presentes
            # ChromaDB não aceita None em metadados
            if chunk.page is not None:
                metadata["page"] = chunk.page
            if chunk.sheet is not None:
                metadata["sheet"] = chunk.sheet
            if chunk.row_start is not None:
                metadata["row_start"] = chunk.row_start
            if chunk.row_end is not None:
                metadata["row_end"] = chunk.row_end
            metadatas.append(metadata)

        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise RuntimeError(f"Falha ao adicionar blocos ao armazenamento de vetores: {exc}") from exc

        return len(chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_id: str | None = None,
    ) -> list[VectorMatch]:
        """
        Busca os chunks mais similares a um vetor de consulta.

        Args:
            query_embedding: Vetor da pergunta do usuário
            top_k: Número máximo de resultados
            document_id: Se fornecido, filtra resultados para este documento

        Returns:
            Lista de VectorMatch ordenada por relevância (maior score primeiro)

        Raises:
            RuntimeError: Se houver erro na comunicação com o ChromaDB
        """
        collection = self._get_collection()

        # Prepara filtro de metadados se document_id foi especificado
        where_filter = None
        if document_id is not None:
            where_filter = {"document_id": document_id}

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise RuntimeError(f"Falha ao consultar o armazenamento de vetores: {exc}") from exc

        matches: list[VectorMatch] = []

        # results contém listas de listas (uma por query, mas só temos uma)
        ids_list = results.get("ids", [[]])[0]
        documents_list = results.get("documents", [[]])[0]
        metadatas_list = results.get("metadatas", [[]])[0]
        distances_list = results.get("distances", [[]])[0]

        for idx, document_id_result in enumerate(ids_list):
            metadata = metadatas_list[idx] if idx < len(metadatas_list) else {}
            distance = distances_list[idx] if idx < len(distances_list) else 1.0

            # Converte distância coseno para score de similaridade (0-1)
            score = 1.0 - float(distance)

            matches.append(
                VectorMatch(
                    document_id=metadata.get("document_id", ""),
                    filename=metadata.get("filename", ""),
                    mime_type=metadata.get("mime_type", ""),
                    document_type=metadata.get("document_type", "unknown"),
                    text=documents_list[idx] if idx < len(documents_list) else "",
                    chunk_index=metadata.get("chunk_index", 0),
                    score=score,
                    page=metadata.get("page"),
                    sheet=metadata.get("sheet"),
                    row_start=metadata.get("row_start"),
                    row_end=metadata.get("row_end"),
                )
            )

        # Ordena por score decrescente
        matches.sort(key=lambda match: match.score, reverse=True)
        return matches

    def delete_all(self) -> int:
        """
        Remove todos os chunks vetoriais da coleção.

        Returns:
            Número de chunks removidos

        Raises:
            RuntimeError: Se houver erro na comunicação com o ChromaDB
        """
        collection = self._get_collection()

        try:
            # Busca todos os IDs na coleção
            results = collection.get(include=[])
            ids_list = results.get("ids", [])
            if not ids_list:
                return 0
            
            # Deleta em lotes para evitar limites do ChromaDB (~5461 por operação)
            batch_size = 1000
            total_deleted = 0
            for i in range(0, len(ids_list), batch_size):
                batch = ids_list[i:i + batch_size]
                collection.delete(ids=batch)
                total_deleted += len(batch)
            
            return total_deleted
        except Exception as exc:
            raise RuntimeError(f"Falha ao deletar todos os chunks: {exc}") from exc

    def delete_by_document_id(self, document_id: str) -> int:
        """
        Remove todos os chunks vetoriais associados a um documento.

        Consulta a coleção por metadados com document_id igual ao fornecido,
        coleta todos os IDs dos chunks e os remove da coleção.

        Args:
            document_id: UUID do documento cujos chunks serão removidos

        Returns:
            Número de chunks removidos

        Raises:
            RuntimeError: Se houver erro na comunicação com o ChromaDB
        """
        collection = self._get_collection()

        try:
            # Busca todos os chunks do documento sem limite de resultados
            results = collection.get(
                where={"document_id": document_id},
                include=[],  # Só precisamos dos IDs
            )
        except Exception as exc:
            raise RuntimeError(f"Falha ao buscar chunks para deleção: {exc}") from exc

        ids_list = results.get("ids", [])
        if not ids_list:
            return 0

        try:
            collection.delete(ids=ids_list)
        except Exception as exc:
            raise RuntimeError(f"Falha ao deletar chunks do armazenamento de vetores: {exc}") from exc

        return len(ids_list)

