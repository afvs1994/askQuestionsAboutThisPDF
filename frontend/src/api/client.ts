const DEFAULT_API_BASE_URL = 'http://localhost:8000';

export interface DocumentSummary {
  id: string;
  filename: string;
  mime_type: string;
  document_type: string;
  chunk_count: number;
  created_at: string;
}

export interface ChatSource {
  page?: number;
  sheet?: string;
  chunk?: number;
  excerpt: string;
  score: number;
  document_id?: string;
  filename?: string;
}

export interface ChatRequest {
  question: string;
  document_id?: string;
  top_k?: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export interface UploadResponse {
  message?: string;
  documents?: DocumentSummary[];
}

function getApiBaseUrl(): string {
  const value = import.meta.env.VITE_API_BASE_URL;
  if (typeof value === 'string' && value.trim().length > 0) {
    return value.trim().replace(/\/+$/, '');
  }

  return DEFAULT_API_BASE_URL;
}

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function getString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined;
}

function getNumber(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

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

export async function fetchDocuments(): Promise<DocumentSummary[]> {
  const response = await fetch(buildApiUrl('/api/documents'), {
    cache: 'no-store'
  });
  const json = await readJsonResponse(response);
  return normalizeDocumentsResponse(json);
}

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

export function formatDocumentScope(document: DocumentSummary | undefined): string {
  return document === undefined ? 'Entire repository' : document.filename;
}