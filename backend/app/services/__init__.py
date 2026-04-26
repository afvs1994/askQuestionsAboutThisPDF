"""
Pacote de serviços da aplicação RAG.

Contém a implementação do pipeline completo de processamento:
- file_loader: Extração de texto de PDFs, DOCXs e XLSXs
- chunking: Divisão inteligente de textos em chunks
- embeddings: Geração de vetores semânticos via sentence-transformers
- vector_store: Armazenamento e busca por similaridade no ChromaDB
- llm: Comunicação com modelos de linguagem via Ollama
- rag: Orquestração do pipeline completo (ingestão + resposta)
"""

