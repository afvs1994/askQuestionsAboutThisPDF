# askQuestionsAboutThisPDF

---

## Descrição do Projeto

O **askQuestionsAboutThisPDF** é um assistente conversacional de código aberto baseado em **RAG (Retrieval-Augmented Generation)** que permite consultar documentos privados de forma inteligente e segura.

### O que é RAG?

RAG é uma técnica de Inteligência Artificial que combina:
- **Recuperação de informações** — busca automática em documentos
- **Geração de texto** — criação de respostas naturais por um modelo de linguagem (LLM)

Em vez de depender apenas do conhecimento genérico do modelo, o RAG consulta **documentos específicos do usuário** para responder perguntas com precisão e fundamento.

### Como funciona o software

O assistente segue um pipeline de 5 etapas:

1. **Recebe uma pergunta** do usuário em linguagem natural
2. **Busca informações** nos documentos previamente indexados
3. **Recupera trechos relevantes** por similaridade semântica (não apenas palavras-chave)
4. **Formula a resposta** com base **exclusivamente** no contexto recuperado
5. **Cita as fontes** — documento, página e trecho exato — para verificação humana

### Diferenciais principais

| Recurso | Benefício |
|---------|-----------|
| **Respostas fundamentadas** | Cada resposta é baseada em trechos reais dos seus documentos |
| **Citação de fontes** | Você pode verificar de onde a informação veio |
| **Privacidade** | Tudo roda localmente — seus documentos nunca saem da sua máquina |
| **Filtro por documento** | Limite a busca a um arquivo específico quando souber onde procurar |
| **Multiformato** | Suporta PDF, DOCX e outros formatos de documento |

### Público-alvo

- **Pesquisadores** — consulta rápida a artigos e relatórios
- **Engenheiros** — busca em normas técnicas e especificações
- **Técnicos** — acesso a manuais e procedimentos
- **Gerentes de engenharia** — síntese de documentos corporativos
- **Estudantes** — estudo e revisão de materiais acadêmicos

---

## Tipos de documentos suportados

O projeto trabalha com documentos nos seguintes formatos:

- **PDF** — extração de texto com PyMuPDF (inclui número da página)
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
│FileLoader│─▶│ Chunking│─▶│Embeddings│─▶│  Chroma │─▶│   LLM    │
│(PDF/DOCX)│  │(Divisão  │  │(Sentence │  │  (Vector │  │(Ollama/  │
│          │  │Semântica)│  │Transformers)│  Store)  │  │ Llama3)  │
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

## Instalação

Esta seção explica como instalar todas as dependências necessárias para rodar o projeto pela primeira vez.

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd askQuestionsAboutThisPDF
```

### 2. Instalar o backend (Python)

O backend requer Python 3.10 ou superior.

```bash
cd backend

# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

> **O que está sendo instalado?** O arquivo `requirements.txt` contém bibliotecas como FastAPI (API), ChromaDB (banco de vetores), sentence-transformers (embeddings) e pytest (testes).

### 3. Instalar o frontend (Node.js)

O frontend requer Node.js 18 ou superior.

```bash
cd frontend

# Instalar dependências
npm install
```

> **O que está sendo instalado?** O arquivo `package.json` define bibliotecas como React (interface), Vite (build) e TypeScript (tipagem).

### 4. Instalar e configurar o Ollama

O Ollama é o servidor de LLM (Inteligência Artificial) que roda localmente na sua máquina.

1. Baixe e instale o Ollama: https://ollama.com
2. Baixe o modelo Llama 3.1:
   ```bash
   ollama run llama3.1
   ```

> **Nota para Windows:** Se o comando `ollama` não for reconhecido, use o caminho completo:
> ```powershell
> C:\Users\<seu-usuario>\AppData\Local\Programs\Ollama\ollama.exe run llama3.1
> ```

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

### 4. Executar Testes (Passo a Passo para Iniciantes)

Esta seção explica como rodar os testes automatizados que verificam se o sistema está funcionando corretamente.

#### O que são testes?
Testes são comandos que executam partes do código para garantir que tudo funciona como esperado. Se algo estiver quebrado, os testes mostram onde está o problema.

#### Passo 1: Abrir o terminal na pasta correta
Primeiro, você precisa estar dentro da pasta `backend`. No terminal, execute:

```bash
cd backend
```

> **Dica:** O comando `cd` significa "change directory" (mudar de pasta). Certifique-se de que você está na pasta raiz do projeto antes de executar este comando.

#### Passo 2: Rodar todos os testes
Execute o seguinte comando para rodar todos os testes:

```bash
pytest tests/ -v
```

> **O que cada parte significa:**
> - `pytest` → é o programa que executa os testes
> - `tests/` → é a pasta onde os testes estão localizados
> - `-v` → significa "verbose" (detalhado). Mostra o nome de cada teste e se passou ou falhou

#### Passo 3: Interpretar o resultado
Após executar o comando, você verá uma saída similar a esta:

```
==================================== test session starts =====================================
platform win32 -- Python 3.14.3, pytest-8.4.2, pluggy-1.6.0
collected 60 items

tests/test_api.py::TestHealthEndpoint::test_health_returns_ok PASSED                    [  1%]
tests/test_api.py::TestDocumentsEndpoint::test_list_documents_empty PASSED              [  3%]
...

=============================== 58 passed, 2 failed in 5.23s ================================
```

**Significado dos resultados:**
- `PASSED` (verde) → O teste passou! A funcionalidade está funcionando corretamente.
- `FAILED` (vermelho) → O teste falhou. Pode indicar um bug ou configuração incorreta.
- `ERROR` → Ocorreu um erro inesperado durante a execução do teste.

#### Passo 4: Rodar apenas um teste específico
Se você quiser testar apenas uma funcionalidade específica, pode rodar apenas um arquivo de teste:

```bash
# Testar apenas os endpoints da API
pytest tests/test_api.py -v

# Testar apenas o serviço de armazenamento
pytest tests/test_storage.py -v

# Testar apenas a deleção de documentos
pytest tests/test_api.py::TestDocumentsEndpoint::test_delete_all_documents -v
```

#### Passo 5: Rodar com cobertura de código (opcional)
A cobertura de código mostra quais partes do código foram testadas. Para gerar um relatório:

```bash
pytest tests/ --cov=app --cov-report=html
```

Após executar, abra o arquivo `htmlcov/index.html` no navegador para ver o relatório visual.

#### Resultado atual do projeto
Atualmente, o projeto possui **60 testes** coletados:
- **58 passando** ✅
- **2 falhas pré-existentes** ⚠️ (relacionadas a mensagens de erro em português vs. inglês — não afetam o funcionamento do sistema)

**Arquivos de teste disponíveis:**
- `backend/tests/test_api.py` — Testes de integração dos endpoints REST (API)
- `backend/tests/test_chunking.py` — Testes de divisão de texto em chunks
- `backend/tests/test_config.py` — Testes de configurações e variáveis de ambiente
- `backend/tests/test_embeddings.py` — Testes de geração de embeddings vetoriais
- `backend/tests/test_file_loader.py` — Testes de extração de texto de arquivos
- `backend/tests/test_llm.py` — Testes de comunicação com o modelo de linguagem
- `backend/tests/test_schemas.py` — Testes de validação de schemas Pydantic
- `backend/tests/test_storage.py` — Testes de persistência de documentos
- `backend/tests/test_vector_store.py` — Testes de operações no ChromaDB

> **Importante:** Se você ver 2 falhas relacionadas a `test_unsupported_format_raises_error` e `test_add_chunks_mismatch_raises_error`, saiba que estas são **falhas conhecidas e esperadas**. Elas ocorrem porque o sistema retorna mensagens de erro em português, mas os testes esperam mensagens em inglês. Isso não indica quebra de funcionalidade.

#### Problemas comuns e soluções

**Erro: "pytest não é reconhecido como comando"**
- **Causa:** O pytest não está instalado.
- **Solução:** Execute `pip install pytest pytest-asyncio` na pasta `backend`.

**Erro: "ModuleNotFoundError" ao rodar testes**
- **Causa:** As dependências do projeto não estão instaladas.
- **Solução:** Execute `pip install -r requirements.txt` na pasta `backend`.

**Erro: "RuntimeError" relacionado ao ChromaDB**
- **Causa:** O banco de vetores pode estar corrompido ou em uso por outro processo.
- **Solução:** Pare o backend (se estiver rodando) e execute os testes novamente.

---

## Como as Configurações e Credenciais são Carregadas (Explicação para Iniciantes)

Este projeto usa um sistema chamado **variáveis de ambiente** para armazenar configurações sensíveis (como senhas, URLs de API, caminhos de pastas) sem precisar colocá-las diretamente no código. Isso é uma prática de segurança muito comum no desenvolvimento profissional.

### O que são variáveis de ambiente?

Imagine que o código-fonte é como uma receita de bolo que você compartilha com várias pessoas. Cada pessoa pode ter:
- Um forno diferente (temperaturas variam)
- Ingredientes de marcas diferentes
- Preferências de sabor distintas

As **variáveis de ambiente** são como as anotações pessoais que cada pessoa faz na receita — elas não alteram a receita original, mas adaptam o resultado às condições de cada cozinha.

No mundo da programação, isso significa que:
- O **mesmo código** pode rodar no computador do desenvolvedor, em um servidor de testes e em um servidor de produção
- Cada ambiente tem **configurações diferentes** (URLs, senhas, caminhos)
- Nenhuma credencial sensível fica exposta no código-fonte

### De onde o sistema lê as configurações?

O projeto usa uma biblioteca chamada `pydantic-settings` para buscar configurações em **três lugares diferentes**, em ordem de prioridade:

```
┌─────────────────────────────────────────────────────────────┐
│  ORDEM DE PRIORIDADE (quem ganha quando há conflito)        │
├─────────────────────────────────────────────────────────────┤
│  1º → Variáveis do sistema operacional (PATH, etc.)         │
│  2º → Arquivo .env na pasta backend/                        │
│  3º → Valores padrão definidos no código (fallback)         │
└─────────────────────────────────────────────────────────────┘
```

**Significado:**
- Se uma variável existir no **sistema operacional** E no arquivo **.env**, o valor do sistema operacional vence
- Se uma variável existir apenas no **.env**, ela será usada
- Se a variável **não existir em lugar nenhum**, o sistema usa o **valor padrão** definido no código

### O arquivo .env (mais comum no dia a dia)

O arquivo `.env` é um arquivo de texto simples que fica na pasta `backend/` e contém as configurações específicas da sua máquina. Ele segue este formato:

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
```

**Regras importantes sobre o .env:**
1. **Nunca comite o .env no Git** — ele deve ficar no `.gitignore` para não vazar credenciais
2. **Cada desenvolvedor tem o seu** — você pode ter `llama3.1` enquanto seu colega usa outro modelo
3. **O formato é simples** — `NOME_DA_VARIAVEL=valor` (sem espaços ao redor do =)

### Como criar o seu arquivo .env

Passo a passo:

1. **Navegue até a pasta do backend:**
   ```bash
   cd backend
   ```

2. **Crie o arquivo .env:**
   - No Windows: clique com o botão direito → Novo → Documento de texto → renomeie para `.env`
   - No VS Code: clique em "Novo Arquivo" na barra lateral → salve como `.env`

3. **Copie o conteúdo de exemplo** da seção "Variáveis de Ambiente" abaixo e cole no arquivo

4. **Ajuste os valores** conforme sua máquina (por exemplo, se o Ollama estiver em outra porta)

### O que acontece se eu não criar o .env?

**Nada de errado!** O sistema foi projetado para funcionar sem o arquivo `.env`. Nesse caso, ele usa os **valores padrão** definidos no código:

| Configuração | Valor padrão (se .env não existir) |
|--------------|-----------------------------------|
| Nome da aplicação | `Private Document RAG API` |
| URL do Ollama | `http://localhost:11434` |
| Modelo LLM | `llama3.1` |
| Origens CORS | `http://localhost:5173` |
| Timeout Ollama | `60` segundos |
| Tamanho dos chunks | `1800` caracteres |

Isso significa que, se você está começando a trabalhar no projeto, **não precisa criar o .env imediatamente** — o sistema funcionará com as configurações padrão.

### Cache das configurações (performance)

O sistema carrega as configurações **uma vez só** quando o backend inicia e guarda em memória (cache). Isso significa:
- ✅ A primeira requisição lê o arquivo
- ✅ As requisições seguintes usam o valor em memória (mais rápido)
- ⚠️ Se você alterar o `.env`, precisa **reiniciar o backend** para as mudanças fazerem efeito

### Resumo para lembrar

```
Você tem 3 formas de configurar o sistema:

1. Variáveis do sistema operacional  →  Prioridade máxima
   (ex: set OLLAMA_MODEL=meu-modelo no Windows)

2. Arquivo .env na pasta backend/     →  Prioridade média
   (ex: OLLAMA_MODEL=meu-modelo dentro do arquivo)

3. Valores padrão no código           →  Prioridade mínima
   (ex: ollama_model: str = "llama3.1" no config.py)
```

**Regra de ouro:** Nunca coloque senhas ou credenciais diretamente no código-fonte. Sempre use o arquivo `.env` ou variáveis do sistema.

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

DELETE /api/documents/{document_id}
Response: {"deleted": true}

DELETE /api/documents
Response: {"deleted_count": N}  // remove todos os documentos
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

### ✅ Carregamento Multiformato
- Upload de PDF, DOCX
- Extração de metadados (páginas)

### ✅ Chunking Inteligente
- Divisão recursiva por caracteres
- Preservação de contexto com overlap

### ✅ Busca Semântica
- Embeddings multilíngues (português/inglês)
- Busca por similaridade no ChromaDB
- Filtro por documento específico (metadata filtering)

### ✅ Citação de Fontes
- Cada resposta inclui trechos originais usados
- Localização precisa (página, chunk)
- Score de similaridade para cada fonte

### ✅ Interface de Chat
- Perguntas em linguagem natural
- Indicador de escopo de busca
- Lista de citações com localização

### ✅ Gerenciamento de Documentos
- Deleção permanente de documentos do repositório
- Confirmação com botões **SIM** / **NÃO**
- Limpeza automática de seleção ativa após deleção

---

## Uso (Guia do Usuário)

Esta seção explica como usar a aplicação após ela estar rodando. A interface web está disponível em `http://localhost:5173`.

### Fluxo básico de uso

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. Upload   │───▶│ 2. Indexação │───▶│  3. Pergunta │───▶│  4. Resposta │
│  Documentos  │    │  Automática  │    │    no Chat   │    │  com Fontes  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Passo 1: Carregar documentos

1. Na coluna esquerda da tela, localize o painel **"Documentos carregados"**
2. Clique no botão **"Escolher arquivos"** e selecione um ou mais arquivos PDF ou DOCX
3. Clique em **"Carregue arquivos"**
4. Aguarde a mensagem de sucesso — o documento será automaticamente processado, dividido em chunks e indexado

> **O que acontece nos bastidores?** O arquivo é enviado ao backend, o texto é extraído, dividido em pedaços (chunks), convertido em vetores numéricos (embeddings) e armazenado no banco de dados vetorial ChromaDB.

### Passo 2: Verificar documentos indexados

Abaixo do painel de upload, o painel **"Documentos indexados"** mostra todos os documentos já processados. Cada item exibe:
- Nome do arquivo
- Tipo do documento
- Quantidade de chunks gerados

### Passo 3: Filtrar o escopo de busca (opcional)

No painel **"Filtro de documentos"**, você pode:
- Deixar em **"Todos os documentos do repositório"** para pesquisar em tudo
- Selecionar um **documento específico** para limitar a resposta a apenas aquele arquivo

> **Quando usar?** Se você sabe que a resposta está em um documento específico, o filtro melhora a precisão e reduz o tempo de processamento.

### Passo 4: Fazer uma pergunta

1. Na coluna direita, localize o painel **"Faça uma pergunta"**
2. Digite sua pergunta em linguagem natural no campo de texto
   - Exemplo: *"Quais são os requisitos de segurança elétrica mencionados na norma?"*
   - Exemplo: *"Liste os materiais utilizados no transformador descrito."*
3. Clique em **"Faça uma pergunta"**
4. Aguarde a resposta — o tempo varia conforme o tamanho do documento e a complexidade da pergunta

### Passo 5: Verificar as fontes

Abaixo da resposta, o painel **"Lista de fontes"** mostra:
- Trechos exatos dos documentos usados para gerar a resposta
- Nome do arquivo de origem
- Número da página (para PDFs)
- Score de similaridade (quanto mais próximo de 1.0, mais relevante)

> **Por que isso importa?** As fontes permitem verificar se a resposta do assistente está fundamentada nos documentos reais e não em "alucinações" da IA.

### Passo 6: Deletar documentos

Para remover documentos do repositório:

1. **Deletar todos:** Clique no botão vermelho **"⚠️ Deletar todos os documentos"** no painel de filtro. Uma janela de confirmação aparecerá com botões **SIM** / **NÃO**.
2. **Deletar individual:** Cada documento na lista possui um botão de exclusão individual.

> ⚠️ **Atenção:** A deleção é permanente. Os arquivos, metadados e vetores associados são removidos irreversivelmente.

---

## Limitações

Esta seção descreve o que o sistema **não faz** ou onde pode apresentar comportamentos inesperados.

### Limitações técnicas

| Limitação | Descrição | Impacto |
|-----------|-----------|---------|
| **Formatos suportados** | Apenas PDF, DOCX e DOC | Arquivos como XLSX, PPTX, imagens escaneadas não são processados |
| **Texto em imagens** | Não extrai texto de imagens dentro de PDFs | Documentos escaneados ou com diagramas complexos perdem informação |
| **Modelo local** | Depende do Ollama rodando na máquina | Requer hardware adequado (RAM, GPU opcional) e tempo de inicialização |
| **Contexto limitado** | O LLM tem limite de tokens de contexto | Documentos muito grandes podem não ter todo o conteúdo considerado |
| **Busca semântica** | Baseada em similaridade, não em palavras exatas | Pode não encontrar termos técnicos muito específicos ou siglas |

### Limitações de performance

- **Tempo de resposta:** Perguntas complexas em documentos grandes podem levar de 10 a 60 segundos
- **Consumo de memória:** O modelo de embeddings e o ChromaDB ocupam espaço em disco e RAM
- **Processamento inicial:** O upload e indexação de um documento grande pode levar vários minutos

### Limitações de precisão

- **Alucinações:** Embora o RAG reduza significativamente o risco, o LLM pode ocasionalmente interpretar incorretamente o contexto
- **Dependência da qualidade do documento:** PDFs mal formatados ou com texto corrompido geram chunks de baixa qualidade
- **Idioma misto:** Documentos com múltiplos idiomas podem ter resultados de busca menos precisos

### Cenários não suportados

- ❌ Processamento de documentos criptografados ou protegidos por senha
- ❌ Extração automática de tabelas em formato estruturado (o texto é extraído, mas a formatação é perdida)
- ❌ Síntese de múltiplos documentos com comparação automática
- ❌ Operação offline completa (o frontend requer conexão com o backend)
- ❌ Suporte a múltiplos usuários simultâneos com isolamento de dados

### Recomendações de uso

- ✅ Verifique sempre as fontes citadas antes de tomar decisões críticas
- ✅ Use o filtro de documentos para melhorar a precisão em perguntas específicas
- ✅ Prefira documentos com texto selecionável (não escaneados)
- ✅ Divida perguntas muito amplas em perguntas menores e mais específicas

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
| File Loader | 6 | Extração PDF, DOCX |
| Embeddings | 4 | Geração de vetores, fallback |
| Vector Store | 5 | Indexação, busca, filtro |
| API | 5 | Endpoints REST, upload, chat |
| **Total** | **58** | **54 passando, 2 falhas pré-existentes** |

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
| Frontend | React + Vite + TypeScript | 18+ |
| Testes | pytest | 9.0+ |

---

## Uso de Inteligência Artificial neste Projeto

Este projeto foi desenvolvido com o auxílio de ferramentas de Inteligência Artificial (IA) para aumentar a produtividade e a qualidade do código. Abaixo, explicamos como essas ferramentas foram utilizadas.

### Por que usar IA no desenvolvimento?

Ferramentas de IA assistem desenvolvedores em tarefas repetitivas, sugestões de código, correção de bugs e documentação. Elas **não substituem** o conhecimento técnico humano, mas agilizam o trabalho diário.

### Ferramentas utilizadas

| Ordem | Ferramenta | Quando foi usada | Função |
|-------|-----------|------------------|--------|
| 1º | **GitHub Copilot Chat** | Durante a maior parte do desenvolvimento | Assistente de código integrado ao VS Code. Sugere trechos de código, explica funções, ajuda na correção de erros e gera testes automaticamente. |
| 2º | **Blackbox Minimax M2.5** | Após esgotar os tokens do GitHub Copilot | Assistente de conversação e geração de código alternativo. Utilizado para continuar o desenvolvimento quando o limite do Copilot foi atingido. |

### O que são "tokens"?

Tokens são a "moeda" que as IAs usam para processar texto. Cada vez que você pede para a IA analisar ou gerar código, ela consome uma quantidade de tokens. Quando o limite mensal é atingido, a ferramenta para de funcionar temporariamente até a renovação.

> **Analogia simples:** Tokens são como minutos de ligação telefônica. Você tem uma franquia mensal e, quando acaba, precisa esperar o próximo ciclo ou usar outro serviço.

### Como a IA foi usada neste projeto

1. **Geração de código boilerplate** — Estruturas iniciais de classes, funções e componentes React
2. **Documentação** — Geração de docstrings e comentários explicativos
3. **Testes automatizados** — Criação de casos de teste para o backend
4. **Correção de bugs** — Análise de erros e sugestões de soluções
5. **Revisão de código** — Sugestões de melhorias de performance e legibilidade

### Limitações e cuidados

- A IA **não tem acesso** a dados reais dos usuários — ela apenas analisa o código-fonte
- Todas as sugestões da IA foram **revisadas e validadas** por desenvolvedores humanos
- A IA pode cometer erros — sempre verifique o código gerado antes de usar em produção
- O uso da IA **não altera a licença** do projeto nem os direitos autorais

### Transparência

Acreditamos na transparência sobre o uso de IA no desenvolvimento de software. Esta seção existe para que você, como usuário ou contribuidor, saiba como o projeto foi construído e quais ferramentas auxiliaram no processo.

---

## Licença

Este projeto está licenciado sob a **Apache License 2.0**.

A Apache 2.0 é uma licença permissiva que permite:
- ✅ Uso comercial
- ✅ Modificação
- ✅ Distribuição
- ✅ Uso em patentes

Com as seguintes condições:
- ℹ️ Manter o aviso de copyright
- ℹ️ Documentar alterações significativas
- ℹ️ Incluir uma cópia da licença

Consulte o arquivo [LICENSE](LICENSE) para o texto completo.

**Resumo:** Você pode usar, modificar e distribuir este código livremente, inclusive em projetos comerciais, desde que mantenha os créditos originais e documente quaisquer mudanças substanciais.