from __future__ import annotations

import re
from typing import Sequence

from app.models import DocumentChunk, DocumentSection


class ChunkingService:
    def __init__(self, max_chunk_chars: int, sentence_overlap: int) -> None:
        self.max_chunk_chars = max(200, max_chunk_chars)
        self.sentence_overlap = max(0, sentence_overlap)

    def chunk_sections(self, sections: Sequence[DocumentSection]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        chunk_index = 0

        for section in sections:
            if section.sheet:
                section_chunks = self._chunk_sheet_section(section)
            else:
                section_chunks = self._chunk_prose_section(section)

            for chunk_text, row_start, row_end in section_chunks:
                chunks.append(
                    DocumentChunk(
                        document_id=section.document_id,
                        filename=section.filename,
                        mime_type=section.mime_type,
                        document_type=section.document_type,
                        text=chunk_text,
                        chunk_index=chunk_index,
                        section_index=section.section_index,
                        page=section.page,
                        sheet=section.sheet,
                        row_start=row_start,
                        row_end=row_end,
                    )
                )
                chunk_index += 1

        return chunks

    def _chunk_prose_section(self, section: DocumentSection) -> list[tuple[str, int | None, int | None]]:
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", section.text) if paragraph.strip()]
        if not paragraphs:
            return []

        chunks: list[str] = []
        current_sentences: list[str] = []

        for paragraph in paragraphs:
            sentences = self._split_sentences(paragraph)
            if not sentences:
                sentences = [paragraph]

            for sentence in sentences:
                candidate = current_sentences + [sentence]
                if current_sentences and len(self._join_sentences(candidate)) > self.max_chunk_chars:
                    chunks.append(self._join_sentences(current_sentences))
                    current_sentences = self._carry_over_sentences(current_sentences)
                    candidate = current_sentences + [sentence]
                if not current_sentences and len(sentence) > self.max_chunk_chars:
                    chunks.extend(self._split_long_sentence(sentence))
                    current_sentences = []
                    continue
                current_sentences.append(sentence)

        if current_sentences:
            chunks.append(self._join_sentences(current_sentences))

        return [(chunk_text, section.row_start, section.row_end) for chunk_text in chunks if chunk_text.strip()]

    def _chunk_sheet_section(self, section: DocumentSection) -> list[tuple[str, int | None, int | None]]:
        lines = section.text.splitlines()
        table_start = next((index for index, line in enumerate(lines) if line.strip().startswith("|")), len(lines))
        prefix_lines = lines[:table_start]
        table_lines = lines[table_start:]

        if len(table_lines) < 3:
            return [(self._normalize_chunk_text(section.text), section.row_start, section.row_end)]

        header_lines = table_lines[:2]
        data_lines = table_lines[2:]
        if not data_lines:
            return [(self._normalize_chunk_text(section.text), section.row_start, section.row_end)]

        chunks: list[tuple[str, int | None, int | None]] = []
        start_index = 0

        while start_index < len(data_lines):
            end_index = start_index + 1
            while end_index <= len(data_lines):
                candidate_lines = prefix_lines + header_lines + data_lines[start_index:end_index]
                candidate_text = "\n".join(candidate_lines).strip()
                if len(candidate_text) <= self.max_chunk_chars:
                    end_index += 1
                    continue
                break

            if end_index == start_index + 1:
                end_index = min(start_index + 1, len(data_lines))

            row_start = None
            row_end = None
            if section.row_start is not None:
                row_start = section.row_start + start_index
                row_count = len(data_lines[start_index:end_index])
                row_end = row_start + row_count - 1

            effective_prefix = list(prefix_lines)
            if len(effective_prefix) >= 2 and row_start is not None and row_end is not None:
                effective_prefix[1] = f"Rows: {row_start}-{row_end}"

            chunk_lines = effective_prefix + header_lines + data_lines[start_index:end_index]
            chunk_text = "\n".join(chunk_lines).strip()

            chunks.append((chunk_text, row_start, row_end))
            start_index = end_index

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        normalized = text.replace("\n", " ")
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?。！？])\s+", normalized) if sentence.strip()]
        return sentences

    def _join_sentences(self, sentences: list[str]) -> str:
        return " ".join(sentence.strip() for sentence in sentences if sentence.strip()).strip()

    def _carry_over_sentences(self, sentences: list[str]) -> list[str]:
        if self.sentence_overlap <= 0:
            return []
        return sentences[-self.sentence_overlap :]

    def _split_long_sentence(self, sentence: str) -> list[str]:
        if len(sentence) <= self.max_chunk_chars:
            return [sentence]
        chunks: list[str] = []
        start_index = 0
        step = max(1, self.max_chunk_chars - 200)
        while start_index < len(sentence):
            end_index = min(len(sentence), start_index + self.max_chunk_chars)
            chunks.append(sentence[start_index:end_index].strip())
            start_index += step
        return [chunk for chunk in chunks if chunk]

    def _normalize_chunk_text(self, text: str) -> str:
        return text.strip()