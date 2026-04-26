"""
Testes para o módulo de comunicação com LLM.

Valida a construção de prompts RAG e o tratamento de erros
na comunicação com o Ollama.
"""
from __future__ import annotations

import pytest

from app.services.llm import build_rag_prompt


class TestBuildRagPrompt:
    """Testes para construção de prompts RAG."""

    def test_prompt_contains_question(self) -> None:
        """
        Verifica que a pergunta está presente no prompt.
        """
        question = "What is machine learning?"
        context = ["Machine learning is a subset of AI."]

        prompt = build_rag_prompt(question, context)

        assert question in prompt
        assert "Question:" in prompt

    def test_prompt_contains_context(self) -> None:
        """
        Verifica que o contexto está presente no prompt.
        """
        question = "What is AI?"
        context = ["AI stands for Artificial Intelligence.", "It involves machine learning."]

        prompt = build_rag_prompt(question, context)

        assert "AI stands for Artificial Intelligence." in prompt
        assert "It involves machine learning." in prompt
        assert "Context:" in prompt

    def test_prompt_contains_instructions(self) -> None:
        """
        Verifica que instruções de sistema estão no prompt.
        """
        prompt = build_rag_prompt("Test?", ["Context."])

        assert "based ONLY on the provided context" in prompt
        assert "Do not make up information" in prompt

    def test_empty_context(self) -> None:
        """
        Verifica comportamento com contexto vazio.
        """
        prompt = build_rag_prompt("Test?", [])

        assert "Context:\n" in prompt
        assert "Test?" in prompt

    def test_multiple_context_chunks(self) -> None:
        """
        Verifica que múltiplos chunks são separados corretamente.
        """
        context = ["Chunk one.", "Chunk two.", "Chunk three."]

        prompt = build_rag_prompt("Question?", context)

        # Verifica que os chunks estão separados por delimitadores
        assert prompt.count("---") == 2  # 3 chunks = 2 separadores

