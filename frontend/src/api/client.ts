/**
 * Cliente HTTP para comunicação com o backend da API RAG.
 *
 * Este módulo centraliza todas as chamadas à API REST, incluindo:
 * - Busca de documentos indexados
 * - Upload de novos documentos
 * - Envio de perguntas ao assistente
 *
 * Também fornece funções utilitárias para normalização de dados,
 * garantindo que respostas malformadas do servidor não quebrem a UI.
 */

/** URL base padrão da API quando nenhuma variável de ambiente está definida. */
const DEFAULT_API_BASE_URL = 'http://localhost:8000';

/** Representação resumida de um documento indexado no backend. */
export interface DocumentSummary {
  id: string;
  filename: string;
  mime_type: string;
  document_type: string;
  chunk_count: number;
  created_at: string;
}

/** Representação de uma fonte/citação retornada pelo assistente. */
export interface ChatSource {
  page?: number;
  sheet?: string;
  chunk?: number;
  excerpt: string;
  score: number;
  document_id?: string;
  filename?: string;
}

/** Payload enviado ao backend ao fazer uma pergunta. */
export interface ChatRequest {
  question: string;
  document_id?: string;
  top_k?: number;
}

/** Resposta do backend para uma pergunta do usuário. */
export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

/** Resposta do backend após upload de documentos. */
export interface UploadResponse {
  message?: string;
  documents?: DocumentSummary[];
}

/**
 * Obtém a URL base da API a partir da variável de ambiente VITE_API_BASE_URL.
 * Caso não esteja definida, usa o valor padrão localhost:8000.
 *
 * @returns URL base da API sem barra no final
 */
function getApiBaseUrl(): string {
  const value = import.meta.env.VITE_API_BASE_URL;
  if (typeof value === 'string' && value.trim().length > 0) {
    return value.trim().replace(/\/+$/, '');
  }

  return DEFAULT_API_BASE_URL;
}

/**
 * Constrói a URL completa para um endpoint da API.
 *
 * @param path - Caminho do endpoint (ex: "/api/documents")
 * @returns URL completa
 */
function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}

/**
 * Type guard: verifica se um valor é um objeto (Record<string, unknown>).
 * Útil para validar respostas JSON dinâmicas.
 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

/**
 * Extrai uma string de um valor desconhecido.
 * Retorna undefined se o valor não for uma string.
 */
function getString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined;
}

/**
 * Extrai um número finito de um valor desconhecido.
 * Retorna undefined se o valor não for um número válido.
 */
function getNumber(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

/**
 * Normaliza um objeto JSON para o tipo DocumentSummary.
 * Retorna null se o objeto não contiver todos os campos obrigatórios.
 *
 * @param value - Valor desconhecido vindo da API
 * @returns DocumentSummary válido ou null
 */
function normalizeDocument(value: unknown): DocumentSummary | null {
  if (!isRecord(value)) {
    return null;
  }

  const id = getString(value.id);
  const filename = getString(value.filename);
  const mimeType = getString(value.mime_type);
  const documentType = getString(value.document_type);
  const chunkCount = getNumber(value.chunk_count);
  const createdAt = getString(value.created_at);

  if (
    id === undefined ||
    filename === undefined ||
    mimeType === undefined ||
    documentType === undefined ||
    chunkCount === undefined ||
    createdAt === undefined
  ) {
    return null;
  }

  return {
    id,
    filename,
    mime_type: mimeType,
    document_type: documentType,
    chunk_count: chunkCount,
    created_at: createdAt
  };
}

/**
 * Normaliza um objeto JSON para o tipo ChatSource.
 * Retorna null se o objeto não contiver os campos mínimos obrigatórios.
 *
 * @param value - Valor desconhecido vindo da API
 * @returns ChatSource válido ou null
 */
function normalizeSource(value: unknown): ChatSource | null {
  if (!isRecord(value)) {
    return null;
  }

  const excerpt = getString(value.excerpt);
  const score = getNumber(value.score);

  if (excerpt === undefined || score === undefined) {
    return null;
  }

  const page = getNumber(value.page);
  const chunk = getNumber(value.chunk);
  const sheet = getString(value.sheet);
  const documentId = getString(value.document_id);
  const filename = getString(value.filename);

  return {
    excerpt,
    score,
    page,
    chunk,
    sheet,
    document_id: documentId,
    filename
  };
}

/**
 * Lê e valida a resposta JSON de uma requisição fetch.
 * Lança erro se a resposta HTTP não for OK ou se o JSON for inválido.
 *
 * @param response - Objeto Response do fetch
 * @returns Payload JSON parseado
 */
async function readJsonResponse(response: Response): Promise<unknown> {
  const responseText = await response.text();

  if (!response.ok) {
    const message = responseText.trim().length > 0 ? responseText : `${response.status} ${response.statusText}`;
    throw new Error(message);
  }

  if (responseText.trim().length === 0) {
    return {};
  }

  try {
    return JSON.parse(responseText) as unknown;
  } catch {
    throw new Error('The server returned invalid JSON.');
  }
}

/**
 * Normaliza uma resposta da API que contém uma lista de documentos.
 * Aceita tanto um array direto quanto um objeto com propriedade "documents".
 *
 * @param value - Valor desconhecido vindo da API
 * @returns Array de DocumentSummary válidos
 */
function normalizeDocumentsResponse(value: unknown): DocumentSummary[] {
  if (Array.isArray(value)) {
    return value
      .map(normalizeDocument)
      .filter((document): document is DocumentSummary => document !== null);
  }

  if (isRecord(value) && Array.isArray(value.documents)) {
    return value.documents
      .map(normalizeDocument)
      .filter((document): document is DocumentSummary => document !== null);
  }

  return [];
}

/**
 * Normaliza a resposta de upload de documentos.
 *
 * @param value - Valor desconhecido vindo da API
 * @returns UploadResponse normalizado
 */
function normalizeUploadResponse(value: unknown): UploadResponse {
  if (!isRecord(value)) {
    return {};
  }

  const message = getString(value.message);
  const documents = Array.isArray(value.documents)
    ? value.documents.map(normalizeDocument).filter((document): document is DocumentSummary => document !== null)
    : undefined;

  return {
    ...(message !== undefined ? { message } : {}),
    ...(documents !== undefined ? { documents } : {})
  };
}

/**
 * Normaliza a resposta de chat do assistente.
 *
 * @param value - Valor desconhecido vindo da API
 * @returns ChatResponse com answer e sources garantidos
 */
function normalizeChatResponse(value: unknown): ChatResponse {
  if (!isRecord(value)) {
    return {
      answer: '',
      sources: []
    };
  }

  const answer = getString(value.answer) ?? '';
  const sources = Array.isArray(value.sources)
    ? value.sources.map(normalizeSource).filter((source): source is ChatSource => source !== null)
    : [];

  return {
    answer,
    sources
  };
}

/**
 * Busca a lista de documentos indexados no backend.
 *
 * @returns Promise com array de DocumentSummary
 */
export async function fetchDocuments(): Promise<DocumentSummary[]> {
  const response = await fetch(buildApiUrl('/api/documents'), {
    cache: 'no-store'
  });
  const json = await readJsonResponse(response);
  return normalizeDocumentsResponse(json);
}

/**
 * Envia um ou mais arquivos para ingestão no backend.
 *
 * @param files - Arquivos selecionados pelo usuário
 * @returns Promise com resposta de upload normalizada
 */
export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();

  for (const file of files) {
    formData.append('files', file);
  }

  const response = await fetch(buildApiUrl('/api/documents/upload'), {
    method: 'POST',
    body: formData
  });

  const json = await readJsonResponse(response);
  return normalizeUploadResponse(json);
}

/**
 * Envia uma pergunta ao assistente RAG.
 *
 * @param request - Objeto com a pergunta, ID do documento (opcional) e top_k
 * @returns Promise com a resposta do assistente e suas fontes
 */
export async function submitChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(buildApiUrl('/api/chat'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });

  const json = await readJsonResponse(response);
  return normalizeChatResponse(json);
}

/**
 * Envia uma requisição DELETE para remover um documento do backend.
 *
 * @param documentId - UUID do documento a ser removido
 */
export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(buildApiUrl(`/api/documents/${encodeURIComponent(documentId)}`), {
    method: 'DELETE'
  });
  await readJsonResponse(response);
}

/**
 * Envia uma requisição DELETE para remover todos os documentos do backend.
 */
export async function deleteAllDocuments(): Promise<void> {
  const response = await fetch(buildApiUrl('/api/documents'), {
    method: 'DELETE'
  });
  await readJsonResponse(response);
}

/**
 * Formata o rótulo de escopo para exibição na interface.
 *
 * @param document - Documento selecionado ou undefined (todos)
 * @returns String descritiva do escopo de busca
 */
export function formatDocumentScope(document: DocumentSummary | undefined): string {
  return document === undefined ? 'Todo o repositório' : document.filename;
}

