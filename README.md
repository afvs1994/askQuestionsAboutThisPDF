# askQuestionsAboutThisPDF

Projeto de um assistente conversacional baseado em **RAG (Retrieval-Augmented Generation)** para consulta de documentos privados.

Em vez de responder apenas com base no treinamento geral do modelo, o assistente:

1. Recebe uma pergunta do usuário;
2. Busca informações nos documentos indexados;
3. Recupera trechos relevantes por similaridade semântica;
4. Formula a resposta com base **exclusivamente** no contexto recuperado;
5. Cita as fontes (documento, página, trecho) para verificação.

---

## Tipos de documentos suportados

O projeto trabalha com documentos nos seguintes formatos:

- **PDF** — extração de texto com PyMuPDF (inclui número da página)
- **Planilhas** — `.xlsx`, `.xls` via Pandas/OpenPyXL (preserva relação entre colunas/linhas)
- **Documentos de texto** — `.docx`, `.doc` via python-docx

---

## Arquitetura

O sistema segue o padrão de **Pipeline RAG**:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI       │────▶│   RAGService    │
│   (React+Vite)  │◀────│   (Backend)     │◀────│   (Orquestrador)│
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
    ┌────────────────────────────────────────────────────┼────┐
    │                                                    │    │
    ▼                                                    ▼    ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│FileLoader│─▶│ Chunking │─▶│Embeddings│─▶│  Chroma  │─▶│   LLM    │
│(PDF/DOCX/ │  │(Divisão  │  │(Sentence│  │  (Vector │  │(Ollama/  │
│ XLSX)     │  │Semântica)│  │Transformers)│  Store)  │  │ Llama3)  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Componentes

| Camada | Componente | Tecnologia | Função |
|--------|-----------|------------|--------|
| **Frontend** | React + Vite + TypeScript | Interface de chat, upload e filtros |
| **API** | FastAPI | Endpoints REST para documentos e chat |
| **Ingestão** | FileLoader | PyMuPDF, python-docx, pandas | Extração de texto multiformato |
| **Chunking** | TextSplitter | Recursive Character | Divisão inteligente preservando tabelas |
| **Embeddings** | SentenceTransformers | `paraphrase-multilingual-MiniLM-L12-v2` | Vetores semânticos |
| **Vector Store** | ChromaDB | Persistência local SQLite | Busca por similaridade com metadados |
| **LLM** | Ollama | Llama 3.1 (local) | Geração de respostas com contexto |
| **Storage** | DocumentStorage | JSON + filesystem | Registro e arquivos originais |

---

## Estrutura do Projeto

```
askQuestionsAboutThisPDF/
├── README.md                 # Este arquivo
├── TODO.md                   # Plano de implementação (concluído)
├── backend/                  # API Python (FastAPI)
│   ├── app/
│   │   ├── main.py           # Ponto de entrada FastAPI
│   │   ├── models.py         # Modelos Pydantic (domínio)
│   │   ├── schemas.py        # Schemas de request/response
│   │   ├── api/              # Rotas REST
│   │   │   ├── health.py     # Health check
│   │   │   ├── documents.py  # Listar e upload de documentos
│   │   │   ├── chat.py       # Endpoint de chat RAG
│   │   │   └── router.py     # Agregador de rotas
│   │   ├── core/             # Configurações e infraestrutura
│   │   │   ├── config.py     # Settings (Pydantic-Settings)
│   │   │   ├── dependencies.py  # Injeção de dependências
│   │   │   └── storage.py    # Persistência de documentos
│   │   └── services/         # Lógica de negócio RAG
│   │       ├── rag.py        # Orquestrador do pipeline
│   │       ├── file_loader.py # Extração de texto
│   │       ├── chunking.py   # Divisão em chunks
│   │       ├── embeddings.py # Geração de embeddings
│   │       ├── vector_store.py # ChromaDB wrapper
│   │       └── llm.py        # Comunicação com Ollama
│   ├── tests/                # Suite de testes (58 testes)
│   ├── requirements.txt      # Dependências Python
│   └── Dockerfile            # Container do backend
├── frontend/                 # Aplicação React
│   ├── src/
│   │   ├── App.tsx           # Componente raiz
│   │   ├── main.tsx          # Ponto de entrada
│   │   ├── styles.css        # Design system CSS
│   │   ├── api/client.ts     # Cliente HTTP da API
│   │   └── components/       # Componentes React
│   │       ├── ChatPanel.tsx      # Painel de chat
│   │       ├── UploadPanel.tsx    # Upload de arquivos
│   │       ├── DocumentFilter.tsx # Filtro de documentos
│   │       └── SourceList.tsx     # Citações/fontes
│   ├── package.json
│   └── Dockerfile            # Container do frontend
└── data/                     # Dados gerados em runtime
    ├── documents.json        # Registro de documentos
    ├── uploads/              # Arquivos originais
    └── chroma/               # Banco de vetores ChromaDB
```

---

## Como Executar

### Pré-requisitos

- Python 3.10+
- Node.js 18+
- Ollama instalado e rodando (para o LLM local)

### 1. Instalar Ollama e baixar o modelo

```bash
# Instale o Ollama: https://ollama.com
ollama run llama3.1
```

> **Nota para Windows:** o Ollama pode não estar automaticamente no `PATH` do sistema. Se o comando `ollama` não for reconhecido, use o caminho completo:
> ```powershell
> C:\Users\<seu-usuario>\AppData\Local\Programs\Ollama\ollama.exe run llama3.1
> ```
> Além disso, o **servidor** Ollama precisa estar em execução (porta 11434). O ícone da bandeja (`ollama app.exe`) sozinho não basta. Inicie o servidor com:
> ```powershell
> ollama serve
> ```

### 2. Iniciar tudo de uma vez (Windows)

Para conveniência, existe um script batch que verifica o Ollama e sobe backend + frontend automaticamente:

```batch
start_app.bat
```

Isso abrirá duas janelas de terminal:
- **Backend** em `http://localhost:8000`
- **Frontend** em `http://localhost:5173`

### 3. Backend manualmente (Python)

```bash
cd backend

# Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar em modo desenvolvimento
uvicorn app.main:app --reload --port 8000
```

O backend estará disponível em `http://localhost:8000`.

### 4. Frontend manualmente (React)

```bash
cd frontend

# Instalar dependências
npm install

# Executar em modo desenvolvimento
npm run dev
```

O frontend estará disponível em `http://localhost:5173`.

### 4. Executar Testes

```bash
cd backend

# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov-report=html
```

**Resultado atual:** 58 testes passando, 0 falhas.

---

## Variáveis de Ambiente

Crie um arquivo `.env` na pasta `backend/`:

```env
# Nome da aplicação
APP_NAME="Private Document RAG API"

# CORS — origens permitidas (separadas por vírgula)
CORS_ORIGINS="http://localhost:5173,http://localhost:3000"

# Modelo de embeddings (HuggingFace)
EMBEDDING_MODEL="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Configurações do Ollama
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llama3.1"
OLLAMA_TIMEOUT_SECONDS=60

# Tamanho dos chunks
CHUNK_SIZE_CHARS=1800
CHUNK_OVERLAP_SENTENCES=1

# Número de resultados na busca vetorial
TOP_K_DEFAULT=5
```

> **Atenção (Windows):** dependendo da versão do `pydantic-settings`, campos do tipo `list[str]` (como `CORS_ORIGINS`) podem causar erro de `JSONDecodeError` ao serem lidos do `.env`. Se isso ocorrer, renomeie ou remova o `.env` — o backend usará os valores padrão do código. Alternativamente, o `config.py` já foi ajustado com `env_parse_json=False` para evitar esse problema.

---

## Troubleshooting

### Ollama não está no PATH (Windows)
Se o comando `ollama` não for reconhecido, o executável provavelmente está em:
```
C:\Users\<seu-usuario>\AppData\Local\Programs\Ollama\ollama.exe
```
Use o caminho completo ou adicione essa pasta às variáveis de ambiente do sistema.

### Servidor Ollama não responde
O ícone do Ollama na bandeja do Windows (`ollama app.exe`) não significa que o **servidor** está ativo. Verifique se a porta 11434 está aberta:
```powershell
netstat -ano | findstr 11434
```
Se não aparecer nada, inicie o servidor manualmente:
```powershell
ollama serve
```

### Erro `JSONDecodeError` ao iniciar o backend
Se o backend crashar com erro no `pydantic_settings` ao ler o `.env`, o problema é o parsing automático de JSON em campos de lista. A solução já foi aplicada no `config.py` (`env_parse_json=False`). Como alternativa imediata, renomeie o arquivo:
```powershell
Rename-Item backend\.env backend\.env.bak
```
O sistema funcionará com os valores padrão definidos no código.

---

## API Endpoints

### Health Check
```
GET /health
Response: {"status": "ok"}
```

### Documentos
```
GET /api/documents
Response: [{"id": "...", "filename": "...", "document_type": "...", "chunk_count": N}]

POST /api/documents/upload
Content-Type: multipart/form-data
Body: files[]
Response: {"documents": [...]}
```

### Chat RAG
```
POST /api/chat
Content-Type: application/json
Body: {
  "question": "Qual é a norma técnica aplicável?",
  "document_id": "abc123",  // opcional — filtra por documento
  "top_k": 5                // opcional — número de chunks
}
Response: {
  "answer": "De acordo com o documento...",
  "sources": [
    {
      "document_id": "abc123",
      "filename": "norma.pdf",
      "page": 12,
      "chunk_index": 3,
      "excerpt": "trecho do texto...",
      "score": 0.8923
    }
  ]
}
```

---

## Funcionalidades Principais

### ✅ Ingestão Multiformato
- Upload de PDF, DOCX, XLSX
- Extração de metadados (página, planilha, linhas)
- Preservação de estrutura tabular em planilhas

### ✅ Chunking Inteligente
- Divisão recursiva por caracteres
- Preservação de contexto com overlap
- Tabelas XLSX mantidas como blocos coesos

### ✅ Busca Semântica
- Embeddings multilíngues (português/inglês)
- Busca por similaridade no ChromaDB
- Filtro por documento específico (metadata filtering)

### ✅ Citação de Fontes
- Cada resposta inclui trechos originais usados
- Localização precisa (página, planilha, chunk)
- Score de similaridade para cada fonte

### ✅ Interface de Chat
- Perguntas em linguagem natural
- Indicador de escopo de busca
- Lista de citações com localização

---

## Testes

A suite de testes cobre todos os componentes do sistema:

| Módulo | Testes | Descrição |
|--------|--------|-----------|
| Config | 6 | Validação de CORS, diretórios, defaults |
| Storage | 8 | CRUD de documentos, sanitização |
| Chunking | 9 | Divisão de texto, tabelas, overlap |
| Schemas | 10 | Validação de requests/responses |
| LLM | 5 | Prompt building, erro de conexão |
| File Loader | 6 | Extração PDF, DOCX, XLSX |
| Embeddings | 4 | Geração de vetores, fallback |
| Vector Store | 5 | Indexação, busca, filtro |
| API | 5 | Endpoints REST, upload, chat |
| **Total** | **58** | **100% passando** |

---

## Público-alvo

- **Pesquisadores** — consulta rápida a artigos e relatórios
- **Engenheiros** — busca em normas técnicas e especificações
- **Técnicos** — acesso a manuais e procedimentos
- **Gerentes de engenharia** — síntese de documentos corporativos

---

## Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Linguagem | Python | 3.10+ |
| Framework | FastAPI | 0.115+ |
| Validação | Pydantic | 2.8+ |
| Embeddings | sentence-transformers | 3.0+ |
| Vector DB | ChromaDB | 0.5+ |
| LLM | Ollama + Llama 3.1 | Local |
| PDF | PyMuPDF | 1.24+ |
| DOCX | python-docx | 1.1+ |
| XLSX | Pandas + OpenPyXL | 2.2+ / 3.1+ |
| Frontend | React + Vite + TypeScript | 18+ |
| Testes | pytest | 9.0+ |

---

## Licença

Projeto desenvolvido para fins de pesquisa e engenharia.

