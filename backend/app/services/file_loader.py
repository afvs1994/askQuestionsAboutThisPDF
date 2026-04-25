from __future__ import annotations

import re
from pathlib import Path

from app.models import DocumentSection, DocumentType

SUPPORTED_EXTENSIONS: dict[str, DocumentType] = {
    ".pdf": DocumentType.pdf,
    ".docx": DocumentType.docx,
    ".xlsx": DocumentType.xlsx,
}
SUPPORTED_MIME_TYPES: dict[str, DocumentType] = {
    "application/pdf": DocumentType.pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.docx,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentType.xlsx,
}
XLSX_ROWS_PER_SECTION = 20


class FileLoaderService:
    def detect_document_type(self, filename: str, content_type: str | None = None) -> DocumentType:
        suffix = Path(filename).suffix.lower()
        if suffix in SUPPORTED_EXTENSIONS:
            return SUPPORTED_EXTENSIONS[suffix]
        if content_type and content_type in SUPPORTED_MIME_TYPES:
            return SUPPORTED_MIME_TYPES[content_type]
        raise ValueError(f"Unsupported file type for '{filename}'. Supported formats: PDF, DOCX, XLSX.")

    def load_sections(
        self,
        file_path: Path,
        document_id: str,
        filename: str,
        mime_type: str,
    ) -> list[DocumentSection]:
        document_type = self.detect_document_type(filename, mime_type)
        if document_type == DocumentType.pdf:
            sections = self._load_pdf_sections(file_path, document_id, filename, mime_type, document_type)
        elif document_type == DocumentType.docx:
            sections = self._load_docx_sections(file_path, document_id, filename, mime_type, document_type)
        else:
            sections = self._load_xlsx_sections(file_path, document_id, filename, mime_type, document_type)
        if not sections:
            raise ValueError(f"No extractable text was found in '{filename}'.")
        return sections

    def _load_pdf_sections(
        self,
        file_path: Path,
        document_id: str,
        filename: str,
        mime_type: str,
        document_type: DocumentType,
    ) -> list[DocumentSection]:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required to process PDF files.") from exc

        sections: list[DocumentSection] = []
        section_index = 0
        with fitz.open(str(file_path)) as document:
            for page_number, page in enumerate(document, start=1):
                text = _normalize_text(page.get_text("text"))
                if not text:
                    continue
                sections.append(
                    DocumentSection(
                        document_id=document_id,
                        filename=filename,
                        mime_type=mime_type,
                        document_type=document_type,
                        text=text,
                        section_index=section_index,
                        page=page_number,
                    )
                )
                section_index += 1
        return sections

    def _load_docx_sections(
        self,
        file_path: Path,
        document_id: str,
        filename: str,
        mime_type: str,
        document_type: DocumentType,
    ) -> list[DocumentSection]:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("python-docx is required to process DOCX files.") from exc

        document = Document(str(file_path))
        sections: list[DocumentSection] = []
        current_lines: list[str] = []
        section_index = 0

        for paragraph in document.paragraphs:
            text = _normalize_text(paragraph.text)
            if not text:
                continue

            style_name = getattr(getattr(paragraph, "style", None), "name", "") or ""
            heading_text = _normalize_heading(style_name, text)

            if heading_text is not None:
                if current_lines:
                    sections.append(
                        DocumentSection(
                            document_id=document_id,
                            filename=filename,
                            mime_type=mime_type,
                            document_type=document_type,
                            text="\n\n".join(current_lines).strip(),
                            section_index=section_index,
                        )
                    )
                    section_index += 1
                    current_lines = []
                current_lines.append(heading_text)
                continue

            current_lines.append(text)

        if current_lines:
            sections.append(
                DocumentSection(
                    document_id=document_id,
                    filename=filename,
                    mime_type=mime_type,
                    document_type=document_type,
                    text="\n\n".join(current_lines).strip(),
                    section_index=section_index,
                )
            )

        return sections

    def _load_xlsx_sections(
        self,
        file_path: Path,
        document_id: str,
        filename: str,
        mime_type: str,
        document_type: DocumentType,
    ) -> list[DocumentSection]:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("pandas and openpyxl are required to process XLSX files.") from exc

        workbook = pd.read_excel(str(file_path), sheet_name=None, dtype=object)
        sections: list[DocumentSection] = []
        section_index = 0

        for sheet_name, frame in workbook.items():
            if frame.empty:
                continue

            cleaned_frame = frame.fillna("")
            headers = [self._normalize_header(str(column), column_index=index) for index, column in enumerate(cleaned_frame.columns)]
            rows = cleaned_frame.to_dict(orient="records")
            if not rows:
                continue

            for start_index in range(0, len(rows), XLSX_ROWS_PER_SECTION):
                end_index = min(start_index + XLSX_ROWS_PER_SECTION, len(rows))
                batch_rows = rows[start_index:end_index]
                row_start = start_index + 2
                row_end = row_start + len(batch_rows) - 1
                lines = [
                    f"Sheet: {sheet_name}",
                    f"Rows: {row_start}-{row_end}",
                    "",
                    self._build_markdown_row(["row_number", *headers]),
                    self._build_markdown_separator(len(headers) + 1),
                ]
                for offset, row in enumerate(batch_rows):
                    excel_row_number = row_start + offset
                    row_values = [str(excel_row_number), *[self._stringify_cell(row.get(header, "")) for header in cleaned_frame.columns]]
                    lines.append(self._build_markdown_row(row_values))
                sections.append(
                    DocumentSection(
                        document_id=document_id,
                        filename=filename,
                        mime_type=mime_type,
                        document_type=document_type,
                        text="\n".join(lines).strip(),
                        section_index=section_index,
                        sheet=str(sheet_name),
                        row_start=row_start,
                        row_end=row_end,
                    )
                )
                section_index += 1

        return sections

    def _normalize_header(self, value: str, column_index: int) -> str:
        normalized = _normalize_text(value)
        return normalized if normalized else f"column_{column_index + 1}"

    def _build_markdown_row(self, cells: list[str]) -> str:
        return "| " + " | ".join(_escape_cell(cell) for cell in cells) + " |"

    def _build_markdown_separator(self, column_count: int) -> str:
        return "| " + " | ".join(["---"] * column_count) + " |"

    def _stringify_cell(self, value: object) -> str:
        if value is None:
            return ""
        return _normalize_text(str(value))


def _normalize_text(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value.replace("\u00a0", " "))
    return collapsed.strip()


def _normalize_heading(style_name: str, text: str) -> str | None:
    if not style_name.lower().startswith("heading"):
        return None
    match = re.search(r"(\d+)", style_name)
    level = int(match.group(1)) if match else 1
    level = max(1, min(level, 6))
    return f"{'#' * level} {text}"


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()