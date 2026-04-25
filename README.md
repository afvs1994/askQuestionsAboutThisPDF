# askQuestionsAboutThisPDF

Projeto de um assistente conversacional baseado em **RAG (Retrieval-Augmented Generation)**.

Em vez de responder apenas com base no treinamento geral do modelo, o assistente:

1. recebe uma pergunta do usuário;
2. busca informações em um documento específico;
3. recupera trechos relevantes;
4. formula a resposta com base no conteúdo encontrado.

## Tipos de documentos suportados

O projeto foi pensado para trabalhar com documentos nos seguintes formatos:

- **PDF**
- **Planilhas**: `.xlsx`, `.xls` e formatos similares
- **Documentos de texto**: `.docx`, `.doc` e formatos similares

## Objetivo

A proposta é permitir perguntas e respostas orientadas por um conjunto de documentos, tornando o assistente útil para consulta de conteúdo corporativo, acadêmico ou técnico armazenado em arquivos.

## Tecnologia

A implementação será desenvolvida em **Python**, com bibliotecas voltadas para:

- leitura e extração de conteúdo dos documentos;
- processamento e normalização de texto;
- busca semântica;
- geração de respostas com base no contexto recuperado.

## Conceito principal

O fluxo do sistema segue a lógica de RAG:

- **Ingestão** dos documentos
- **Extração** do conteúdo
- **Indexação** dos trechos relevantes
- **Recuperação** das passagens mais adequadas
- **Geração** da resposta final

## Visão geral

Este repositório servirá como base para a construção de um assistente que responda perguntas com fidelidade ao conteúdo dos arquivos enviados, reduzindo alucinações e aumentando a precisão das respostas.
