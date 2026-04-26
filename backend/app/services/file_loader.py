"""
Extração de texto de documentos multiformato.

Suporta:
- PDF: via PyMuPDF (fitz), extrai texto por página
- DOCX: via python-docx, extrai texto por parágrafo
- XLSX: via pandas/openpyxl, converte planilhas para Markdown

Cada formato retorna uma lista de DocumentSection, preservando
metadados de localização (página, planilha, linhas) para citação.
"""
from __future__ import annotations

import io
import uuid
from pathlib import Path

from app.models import DocumentSection, DocumentType, IncomingFile


def _detect_document_type(filename: str) -> DocumentType:
    """
    Detecta o tipo de documento pela extensão do arquivo.

    Args:
        filename: Nome do arquivo com extensão

    Returns:
        Tipo de documento correspondente
    """
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        return DocumentType.pdf
    if extension in (".docx", ".doc"):
        return DocumentType.docx
    if extension in (".xlsx", ".xls"):
        return DocumentType.xlsx
    return DocumentType.unknown


def _load_pdf_sections(document_id: str, filename: str, content: bytes) -> list[DocumentSection]:
    """
    Extrai texto de um PDF página por página.

    Usa PyMuPDF (fitz) para leitura eficiente de PDFs.
    Cada página vira uma DocumentSection separada.

    Args:
        document_id: UUID do documento
        filename: Nome original do arquivo
        content: Conteúdo binário do PDF

    Returns:
        Lista de seções, uma por página
    """
    import fitz  # PyMuPDF

    sections: list[DocumentSection] = []
    with fitz.open(stream=content, filetype="pdf") as pdf_document:
        for page_index in range(len(pdf_document)):
            page = pdf_document[page_index]
            text = page.get_text().strip()
            if text:
                sections.append(
                    DocumentSection(
                        document_id=document_id,
                        filename=filename,
                        mime_type="application/pdf",
                        document_type=DocumentType.pdf,
                        text=text,
                        section_index=page_index,
                        page=page_index + 1,
                    )
                )
    return sections


def _load_docx_sections(document_id: str, filename: str, content: bytes) -> list[DocumentSection]:
    """
    Extrai texto de um documento DOCX.

    Usa python-docx para ler parágrafos. Todo o texto é agrupado
    em uma única seção, pois a localização por parágrafo não é
    tão relevante quanto em PDFs.

    Args:
        document_id: UUID do documento
        filename: Nome original do arquivo
        content: Conteúdo binário do DOCX

    Returns:
        Lista com uma única seção contendo todo o texto
    """
    from docx import Document

    document = Document(io.BytesIO(content))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]

    if not paragraphs:
        return []

    return [
        DocumentSection(
            document_id=document_id,
            filename=filename,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            document_type=DocumentType.docx,
            text="\n\n".join(paragraphs),
            section_index=0,
        )
    ]


def _load_xlsx_sections(document_id: str, filename: str, content: bytes) -> list[DocumentSection]:
    """
    Extrai texto de planilhas Excel convertendo para Markdown.

    Usa pandas para ler cada planilha e converte para tabela Markdown,
    preservando a estrutura tabular e relações entre colunas.
    Cada planilha vira uma DocumentSection separada.

    Args:
        document_id: UUID do documento
        filename: Nome original do arquivo
        content: Conteúdo binário do XLSX

    Returns:
        Lista de seções, uma por planilha
    """
    import pandas as pd

    sections: list[DocumentSection] = []
    excel_file = pd.ExcelFile(io.BytesIO(content))

    for sheet_index, sheet_name in enumerate(excel_file.sheet_names):
        dataframe = pd.read_excel(excel_file, sheet_name=sheet_name)
        if dataframe.empty:
            continue

        # Converte DataFrame para tabela Markdown
        markdown_table = dataframe.to_markdown(index=False)

        sections.append(
            DocumentSection(
                document_id=document_id,
                filename=filename,
                mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                document_type=DocumentType.xlsx,
                text=f"Sheet: {sheet_name}\n\n{markdown_table}",
                section_index=sheet_index,
                sheet=sheet_name,
                row_start=1,
                row_end=len(dataframe),
            )
        )

    return sections


def load_file_sections(incoming_file: IncomingFile) -> list[DocumentSection]:
    """
    Extrai seções de texto de um arquivo baseado em seu tipo.

    Dispatcher que delega para o loader específico de cada formato.

    Args:
        incoming_file: Arquivo recebido via upload

    Returns:
        Lista de seções de texto extraídas

    Raises:
        ValueError: Se o formato não for suportado
        RuntimeError: Se houver erro na leitura do arquivo
    """
    document_id = str(uuid.uuid4())
    document_type = _detect_document_type(incoming_file.filename)

    if document_type == DocumentType.unknown:
        raise ValueError(f"Unsupported file format: {incoming_file.filename}")

    try:
        if document_type == DocumentType.pdf:
            return _load_pdf_sections(document_id, incoming_file.filename, incoming_file.content)
        if document_type == DocumentType.docx:
            return _load_docx_sections(document_id, incoming_file.filename, incoming_file.content)
        if document_type == DocumentType.xlsx:
            return _load_xlsx_sections(document_id, incoming_file.filename, incoming_file.content)
    except Exception as exc:
        raise RuntimeError(f"Failed to parse {incoming_file.filename}: {exc}") from exc

    return []

