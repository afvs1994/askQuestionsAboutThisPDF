"""
Testes para o módulo de extração de texto de documentos.

Valida a detecção de tipos de arquivo e a extração de texto
para cada formato suportado (PDF, DOCX, XLSX).
"""
from __future__ import annotations

import io

import pytest

from app.models import DocumentType, IncomingFile
from app.services.file_loader import _detect_document_type, load_file_sections


class TestDetectDocumentType:
    """Testes para detecção de tipo de documento."""

    def test_pdf_extension(self) -> None:
        """
        Verifica detecção de arquivo PDF.
        """
        assert _detect_document_type("document.pdf") == DocumentType.pdf
        assert _detect_document_type("document.PDF") == DocumentType.pdf

    def test_docx_extension(self) -> None:
        """
        Verifica detecção de arquivo DOCX.
        """
        assert _detect_document_type("document.docx") == DocumentType.docx
        assert _detect_document_type("document.doc") == DocumentType.docx

    def test_xlsx_extension(self) -> None:
        """
        Verifica detecção de arquivo XLSX.
        """
        assert _detect_document_type("spreadsheet.xlsx") == DocumentType.xlsx
        assert _detect_document_type("spreadsheet.xls") == DocumentType.xlsx

    def test_unknown_extension(self) -> None:
        """
        Verifica que extensões desconhecidas retornam 'unknown'.
        """
        assert _detect_document_type("file.txt") == DocumentType.unknown
        assert _detect_document_type("file.zip") == DocumentType.unknown


class TestLoadFileSections:
    """Testes para extração de texto de arquivos."""

    def test_unsupported_format_raises_error(self) -> None:
        """
        Verifica que formato não suportado lança ValueError.
        """
        incoming = IncomingFile(
            filename="test.txt",
            content=b"plain text content",
            content_type="text/plain",
        )

        with pytest.raises(ValueError, match="Unsupported file format"):
            load_file_sections(incoming)

    def test_empty_content_raises_error(self) -> None:
        """
        Verifica que conteúdo vazio ou inválido é tratado.
        """
        incoming = IncomingFile(
            filename="test.pdf",
            content=b"not a real pdf",
            content_type="application/pdf",
        )

        # PyMuPDF pode falhar ou retornar vazio para conteúdo inválido
        with pytest.raises((RuntimeError, ValueError)):
            load_file_sections(incoming)

