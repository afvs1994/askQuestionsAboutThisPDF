"""
Testes de integração para os endpoints da API REST.

Valida o comportamento dos endpoints HTTP usando um cliente de teste
async do FastAPI, garantindo que as rotas respondam corretamente.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """
    Cria um cliente de teste síncrono para a aplicação FastAPI.
    
    Inicializa o estado da aplicação com um RAGService funcional
    para que os endpoints possam ser testados corretamente.
    """
    app = create_app()
    
    # Força a inicialização do lifespan para configurar o estado
    with TestClient(app) as test_client:
        yield test_client


class TestHealthEndpoint:
    """Testes para o endpoint de health check."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """
        Verifica que /health retorna status ok.
        """
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestDocumentsEndpoint:
    """Testes para os endpoints de documentos."""

    def test_list_documents_empty(self, client: TestClient) -> None:
        """
        Verifica que lista de documentos vazia é retornada inicialmente.
        """
        response = client.get("/api/documents")

        assert response.status_code == 200
        assert response.json() == []

    def test_upload_no_files(self, client: TestClient) -> None:
        """
        Verifica erro 400 quando nenhum arquivo é enviado.
        """
        response = client.post("/api/documents/upload")

        assert response.status_code == 422  # FastAPI validation error


    def test_delete_all_documents(self, client: TestClient) -> None:
        """
        Verifica que DELETE /api/documents funciona corretamente.
        Remove todos os documentos e retorna contagem.
        """
        response = client.delete("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        assert isinstance(data["deleted_count"], int)

    def test_delete_document_not_found(self, client: TestClient) -> None:
        """
        Verifica erro 404 ao tentar deletar documento inexistente.
        """
        response = client.delete("/api/documents/non-existent-id")
        
        assert response.status_code == 404
        assert "detail" in response.json()


class TestChatEndpoint:
    """Testes para o endpoint de chat."""

    def test_chat_empty_question(self, client: TestClient) -> None:
        """
        Verifica erro de validação para pergunta vazia.
        """
        response = client.post("/api/chat", json={"question": ""})

        assert response.status_code == 422

    def test_chat_valid_question_no_documents(self, client: TestClient) -> None:
        """
        Verifica resposta quando não há documentos indexados.
        """
        response = client.post("/api/chat", json={"question": "What is this?"})

        # Deve retornar 200 com resposta indicando que não encontrou informação
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data

