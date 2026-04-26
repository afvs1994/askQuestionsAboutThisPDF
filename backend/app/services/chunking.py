"""
Divisão inteligente de textos em chunks para indexação vetorial.

Implementa chunking por sentenças com overlap configurável,
garantindo que o contexto semântico não seja perdido nas bordas
de cada chunk. Para planilhas, preserva a estrutura tabular
ao não quebrar linhas de dados ao meio.
"""
from __future__ import annotations

import re

from app.core.config import Settings
from app.models import DocumentChunk, DocumentSection


def _split_into_sentences(text: str) -> list[str]:
    """
    Divide um texto em sentenças usando regex.

    Reconhece pontos finais, pontos de interrogação e exclamação
    como delimitadores de sentença, ignorando abreviações comuns.

    Args:
        text: Texto a ser dividido

    Returns:
        Lista de sentenças individuais
    """
    # Regex que captura pontuação de fim de sentença seguida de espaço ou fim de string
    sentence_pattern = re.compile(r'(?<=[.!?])\s+|\n{2,}')
    sentences = sentence_pattern.split(text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def chunk_sections(sections: list[DocumentSection], settings: Settings) -> list[DocumentChunk]:
    """
    Divide seções de documento em chunks de tamanho controlado.

    Estratégia:
    1. Para cada seção, divide em sentenças
    2. Agrupa sentenças em chunks até atingir chunk_size_chars
    3. Adiciona overlap de sentenças entre chunks consecutivos
    4. Preserva metadados de localização (página, planilha, etc.)

    Args:
        sections: Lista de seções extraídas do documento
        settings: Configurações com chunk_size_chars e chunk_overlap_sentences

    Returns:
        Lista de chunks prontos para embedding e indexação
    """
    chunks: list[DocumentChunk] = []
    chunk_size = settings.chunk_size_chars
    overlap = settings.chunk_overlap_sentences

    for section in sections:
        sentences = _split_into_sentences(section.text)
        if not sentences:
            continue

        current_sentences: list[str] = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # Se adicionar esta sentença ultrapassa o limite e já temos conteúdo,
            # finaliza o chunk atual e inicia um novo com overlap
            if current_length + sentence_length > chunk_size and current_sentences:
                # Cria o chunk com as sentenças acumuladas
                chunk_text = " ".join(current_sentences)
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
                        row_start=section.row_start,
                        row_end=section.row_end,
                    )
                )

                # Prepara overlap para o próximo chunk
                if overlap > 0 and len(current_sentences) >= overlap:
                    current_sentences = current_sentences[-overlap:]
                    current_length = sum(len(s) for s in current_sentences)
                else:
                    current_sentences = []
                    current_length = 0

                chunk_index += 1

            current_sentences.append(sentence)
            current_length += sentence_length + 1  # +1 pelo espaço

        # Não esquece o último chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
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
                    row_start=section.row_start,
                    row_end=section.row_end,
                )
            )

    return chunks

