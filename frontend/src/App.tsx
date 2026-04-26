/**
 * Componente raiz da aplicação de RAG (Retrieval-Augmented Generation).
 *
 * Responsável por orquestrar toda a interface do usuário, incluindo:
 * - Upload de documentos (PDF, DOCX, XLSX)
 * - Listagem e filtro de documentos indexados
 * - Interface de chat com perguntas e respostas
 * - Exibição das fontes/citações das respostas
 *
 * Gerencia o estado global da aplicação e coordena as chamadas à API.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ChatSource, DocumentSummary, fetchDocuments, formatDocumentScope, submitChat, uploadDocuments } from './api/client';
import ChatPanel from './components/ChatPanel';
import DocumentFilter from './components/DocumentFilter';
import SourceList from './components/SourceList';
import UploadPanel from './components/UploadPanel';

/**
 * Extrai uma mensagem de erro legível de qualquer valor lançado.
 * Útil para normalizar erros de API, exceções JavaScript, etc.
 *
 * @param error - Valor capturado em um bloco catch
 * @param fallbackMessage - Mensagem padrão caso não consiga extrair o erro
 * @returns Mensagem de erro amigável para exibição ao usuário
 */
function getErrorMessage(error: unknown, fallbackMessage: string): string {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallbackMessage;
}

/**
 * Componente principal da aplicação.
 *
 * Mantém o estado de todos os documentos, seleção atual, estado de carregamento
 * e respostas do chat. Coordena a comunicação entre painéis via props.
 */
export default function App() {
  /** Lista de documentos indexados no backend. */
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);

  /** ID do documento selecionado no filtro (string vazia = todos os documentos). */
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>('');

  /** Indica se a lista de documentos está sendo carregada. */
  const [isDocumentsLoading, setIsDocumentsLoading] = useState<boolean>(true);

  /** Mensagem de erro ao carregar documentos, ou null se não houver erro. */
  const [documentsError, setDocumentsError] = useState<string | null>(null);

  /** Indica se há um upload em andamento. */
  const [isUploading, setIsUploading] = useState<boolean>(false);

  /** Mensagem de erro no upload, ou null se não houver erro. */
  const [uploadError, setUploadError] = useState<string | null>(null);

  /** Indica se uma pergunta está sendo processada pelo backend. */
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);

  /** Mensagem de erro no chat, ou null se não houver erro. */
  const [chatError, setChatError] = useState<string | null>(null);

  /** Resposta textual do assistente à última pergunta. */
  const [chatAnswer, setChatAnswer] = useState<string>('');

  /** Lista de fontes/citações que embasaram a última resposta. */
  const [chatSources, setChatSources] = useState<ChatSource[]>([]);

  /**
   * Documento atualmente selecionado, derivado da lista e do ID selecionado.
   * Retorna undefined quando nenhum documento está selecionado (escopo = todos).
   */
  const selectedDocument = useMemo(() => {
    return documents.find((document) => document.id === selectedDocumentId);
  }, [documents, selectedDocumentId]);

  /** Rótulo descritivo do escopo de busca atual (ex: "Entire repository" ou nome do arquivo). */
  const scopeLabel = formatDocumentScope(selectedDocument);

  /**
   * Busca a lista de documentos do backend.
   * Usa useCallback para manter referência estável entre renderizações.
   */
  const refreshDocuments = useCallback(async (): Promise<void> => {
    setIsDocumentsLoading(true);
    setDocumentsError(null);

    try {
      const fetchedDocuments = await fetchDocuments();
      setDocuments(fetchedDocuments);
    } catch (error) {
      setDocumentsError(getErrorMessage(error, 'Falha ao carregar os documentos.'));
    } finally {
      setIsDocumentsLoading(false);
    }
  }, []);

  /** Efeito para carregar documentos na montagem inicial do componente. */
  useEffect(() => {
    void refreshDocuments();
  }, [refreshDocuments]);

  /**
   * Efeito para limpar a seleção caso o documento selecionado seja removido.
   * Ex: usuário deleta um documento que estava selecionado no filtro.
   */
  useEffect(() => {
    if (selectedDocumentId.length === 0) {
      return;
    }

    const selectionStillExists = documents.some((document) => document.id === selectedDocumentId);
    if (!selectionStillExists) {
      setSelectedDocumentId('');
    }
  }, [documents, selectedDocumentId]);

  /**
   * Handler para upload de novos documentos.
   * Envia os arquivos ao backend e atualiza a lista local.
   *
   * @param files - Arquivos selecionados pelo usuário
   */
  async function handleUpload(files: File[]): Promise<void> {
    setIsUploading(true);
    setUploadError(null);

    try {
      await uploadDocuments(files);
      await refreshDocuments();
    } catch (error) {
      const message = getErrorMessage(error, 'Falha ao carregar os documentos.');
      setUploadError(message);
      throw error;
    } finally {
      setIsUploading(false);
    }
  }

  /**
   * Handler para envio de uma pergunta ao assistente.
   * Envia a pergunta ao backend junto com o filtro de documento (se houver).
   *
   * @param question - Pergunta digitada pelo usuário
   */
  async function handleChatSubmit(question: string): Promise<void> {
    setIsChatLoading(true);
    setChatError(null);
    setChatAnswer('');
    setChatSources([]);

    try {
      const response = await submitChat({
        question,
        document_id: selectedDocumentId.length > 0 ? selectedDocumentId : undefined,
        top_k: 5
      });

      setChatAnswer(
        response.answer.length > 0 ? response.answer : 'Nenhuma respota foi retornada pra esta pergunta.'
      );
      setChatSources(response.sources);
    } catch (error) {
      const message = getErrorMessage(error, 'Falha em submeter a pergunta.');
      setChatError(message);
      throw error;
    } finally {
      setIsChatLoading(false);
    }
  }

  return (
    <div className="app-shell">
      {/* Cabeçalho da aplicação com título e descrição */}
      <header className="app-header">
        <div>
          <p className="eyebrow">Assistente conversacional baseado em RAG (Retrieval-Augmented Generation)</p>
          <h1>Faça perguntas sobre os documentos carregados</h1>
        </div>
        <p className="app-description">
          Carregue arquivos PDF ou DOCX, faça perguntas e receba respostas com citações do conteúdo indexado.
        </p>
      </header>

      <main className="app-grid">
        {/* Coluna esquerda: upload, listagem e filtro de documentos */}
        <div className="column-stack">
          <UploadPanel errorMessage={uploadError} isUploading={isUploading} onUpload={handleUpload} />

          {/* Painel de listagem de documentos indexados */}
          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Repositório</p>
                <h2>Documentos indexados</h2>
              </div>
            </div>

            {documentsError !== null ? <p className="error-message">{documentsError}</p> : null}
            {isDocumentsLoading ? <p className="muted-text">Loading document library...</p> : null}
            {!isDocumentsLoading && documents.length === 0 && documentsError === null ? (
              <p className="muted-text">Nenhum documento indexado ainda. Carregue um arquivo para iniciar.</p>
            ) : null}
            {documents.length > 0 ? (
              <ul className="document-summary-list">
                {documents.map((document) => (
                  <li className="document-summary-item" key={document.id}>
                    <div className="document-summary-main">
                      <h3>{document.filename}</h3>
                      <p>
                        {document.document_type} · {document.chunk_count} chunks
                      </p>
                    </div>
                    <span className="document-summary-metadata">{document.mime_type}</span>
                  </li>
                ))}
              </ul>
            ) : null}
          </section>

          <DocumentFilter
            documents={documents}
            isLoading={isDocumentsLoading}
            selectedDocumentId={selectedDocumentId}
            onChange={setSelectedDocumentId}
          />
        </div>

        {/* Coluna direita: chat e fontes */}
        <div className="column-stack">
          <ChatPanel
            answer={chatAnswer}
            errorMessage={chatError}
            isLoading={isChatLoading}
            scopeLabel={scopeLabel}
            onSubmit={handleChatSubmit}
          />

          <SourceList sources={chatSources} />
        </div>
      </main>
    </div>
  );
}

