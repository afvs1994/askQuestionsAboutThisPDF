"""
Persistência de metadados e arquivos originais dos documentos.

O DocumentStorage gerencia:
- Salvamento dos arquivos originais enviados pelo usuário
- Registro de metadados em JSON (documents.json)
- Listagem e recuperação de documentos indexados

Todas as operações de escrita no registry são thread-safe via Lock.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from threading import Lock
from typing import Sequence

from app.core.config import Settings
from app.models import StoredDocument

# Regex para sanitizar nomes de arquivo (remove caracteres perigosos)
_FILENAME_SANITIZER = re.compile(r"[^A-Za-z0-9._-]+")


class DocumentStorage:
    """
    Gerenciador de persistência de documentos.

    Mantém uma cópia dos arquivos originais no diretório de uploads
    e um registro JSON com metadados de todos os documentos indexados.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Inicializa o storage com as configurações da aplicação.

        Args:
            settings: Configurações com os caminhos de diretórios
        """
        self.settings = settings
        self.data_dir = settings.data_dir
        self.upload_dir = settings.upload_dir
        self.chroma_dir = settings.chroma_dir
        self.registry_file = settings.registry_file
        self._lock = Lock()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """
        Garante que todos os diretórios necessários existam.
        Cria os diretórios de dados, uploads, chroma e o pai do registry.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

    def save_original_file(self, document_id: str, filename: str, content: bytes) -> Path:
        """
        Salva o arquivo original enviado pelo usuário.

        O arquivo é armazenado em um subdiretório identificado pelo document_id
        para evitar colisões de nome entre documentos diferentes.

        Args:
            document_id: UUID do documento
            filename: Nome original do arquivo
            content: Conteúdo binário do arquivo

        Returns:
            Caminho absoluto onde o arquivo foi salvo
        """
        safe_filename = self._sanitize_filename(filename)
        document_dir = self.upload_dir / document_id
        document_dir.mkdir(parents=True, exist_ok=True)
        target_path = document_dir / safe_filename
        target_path.write_bytes(content)
        return target_path

    def list_documents(self) -> list[StoredDocument]:
        """
        Retorna todos os documentos registrados, ordenados por data de criação
        decrescente (mais recentes primeiro).

        Returns:
            Lista de StoredDocument
        """
        documents = self._load_documents()
        return sorted(documents, key=lambda document: document.created_at, reverse=True)

    def get_document(self, document_id: str) -> StoredDocument | None:
        """
        Busca um documento específico pelo ID.

        Args:
            document_id: UUID do documento

        Returns:
            StoredDocument se encontrado, None caso contrário
        """
        for document in self._load_documents():
            if document.id == document_id:
                return document
        return None

    def upsert_document(self, document: StoredDocument) -> None:
        """
        Adiciona ou atualiza um documento no registro.

        Se o documento já existir (mesmo ID), é substituído.
        A operação é thread-safe.

        Args:
            document: Documento a ser registrado
        """
        with self._lock:
            documents = self._load_documents()
            kept_documents = [existing for existing in documents if existing.id != document.id]
            kept_documents.append(document)
            kept_documents.sort(key=lambda item: item.created_at, reverse=True)
            self._write_documents(kept_documents)

    def _load_documents(self) -> list[StoredDocument]:
        """
        Carrega a lista de documentos do arquivo JSON.

        Returns:
            Lista de StoredDocument (vazia se o arquivo não existir)

        Raises:
            RuntimeError: Se o arquivo JSON estiver malformado
        """
        if not self.registry_file.exists():
            return []
        raw_text = self.registry_file.read_text(encoding="utf-8").strip()
        if not raw_text:
            return []
        payload = json.loads(raw_text)
        if not isinstance(payload, list):
            raise RuntimeError(f"O registro de documentos está corrompido: {self.registry_file}")
        documents: list[StoredDocument] = []
        for item in payload:
            if isinstance(item, dict):
                documents.append(StoredDocument.model_validate(item))
        return documents

    def _write_documents(self, documents: Sequence[StoredDocument]) -> None:
        """
        Persiste a lista de documentos no arquivo JSON.

        Usa escrita atômica (arquivo temporário + rename) para evitar
        corrupção em caso de falha durante a escrita.

        Args:
            documents: Lista de documentos a persistir
        """
        payload = [document.model_dump(mode="json") for document in documents]
        temp_path = self.registry_file.with_suffix(self.registry_file.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.registry_file)

    def delete_document(self, document_id: str) -> bool:
        """
        Remove um documento do registro e apaga seus arquivos originais.

        A operação é thread-safe e atômica para o registry JSON.
        O diretório de uploads do documento é removido recursivamente.

        Args:
            document_id: UUID do documento a ser removido

        Returns:
            True se o documento existia e foi removido, False caso contrário
        """
        with self._lock:
            documents = self._load_documents()
            original_count = len(documents)
            # Filtra o documento a ser removido
            kept_documents = [existing for existing in documents if existing.id != document_id]
            if len(kept_documents) == original_count:
                # Documento não encontrado no registry
                return False
            # Reescreve o registry sem o documento removido
            self._write_documents(kept_documents)

        # Remove o diretório de uploads do documento (fora do lock pois é I/O de filesystem)
        document_dir = self.upload_dir / document_id
        if document_dir.exists():
            import shutil
            shutil.rmtree(document_dir, ignore_errors=True)

        return True

    def delete_all_documents(self) -> int:
        """
        Remove todos os documentos do registro e apaga todos os arquivos originais.

        A operação é thread-safe e atômica para o registry JSON.
        Todos os diretórios de uploads são removidos recursivamente.

        Returns:
            Número de documentos removidos
        """
        with self._lock:
            documents = self._load_documents()
            count = len(documents)
            # Limpa o registry
            self._write_documents([])

        # Remove todos os diretórios de uploads (fora do lock)
        if self.upload_dir.exists():
            import shutil
            for item in self.upload_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)

        return count

    def _sanitize_filename(self, filename: str) -> str:
        """
        Remove caracteres perigosos do nome do arquivo.

        Args:
            filename: Nome original do arquivo

        Returns:
            Nome sanitizado seguro para uso no filesystem
        """
        clean_name = Path(filename).name.strip()
        if not clean_name:
            clean_name = "upload"
        return _FILENAME_SANITIZER.sub("_", clean_name)

