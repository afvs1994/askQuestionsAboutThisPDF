import { useCallback, useEffect, useMemo, useState } from 'react';
import { ChatSource, DocumentSummary, fetchDocuments, formatDocumentScope, submitChat, uploadDocuments } from './api/client';
import ChatPanel from './components/ChatPanel';
import DocumentFilter from './components/DocumentFilter';
import SourceList from './components/SourceList';
import UploadPanel from './components/UploadPanel';

function getErrorMessage(error: unknown, fallbackMessage: string): string {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallbackMessage;
}

export default function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>('');
  const [isDocumentsLoading, setIsDocumentsLoading] = useState<boolean>(true);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [chatAnswer, setChatAnswer] = useState<string>('');
  const [chatSources, setChatSources] = useState<ChatSource[]>([]);

  const selectedDocument = useMemo(() => {
    return documents.find((document) => document.id === selectedDocumentId);
  }, [documents, selectedDocumentId]);

  const scopeLabel = formatDocumentScope(selectedDocument);

  const refreshDocuments = useCallback(async (): Promise<void> => {
    setIsDocumentsLoading(true);
    setDocumentsError(null);

    try {
      const fetchedDocuments = await fetchDocuments();
      setDocuments(fetchedDocuments);
    } catch (error) {
      setDocumentsError(getErrorMessage(error, 'Unable to load documents.'));
    } finally {
      setIsDocumentsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshDocuments();
  }, [refreshDocuments]);

  useEffect(() => {
    if (selectedDocumentId.length === 0) {
      return;
    }

    const selectionStillExists = documents.some((document) => document.id === selectedDocumentId);
    if (!selectionStillExists) {
      setSelectedDocumentId('');
    }
  }, [documents, selectedDocumentId]);

  async function handleUpload(files: File[]): Promise<void> {
    setIsUploading(true);
    setUploadError(null);

    try {
      await uploadDocuments(files);
      await refreshDocuments();
    } catch (error) {
      const message = getErrorMessage(error, 'Failed to upload documents.');
      setUploadError(message);
      throw error;
    } finally {
      setIsUploading(false);
    }
  }

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
        response.answer.length > 0 ? response.answer : 'No answer was returned for this question.'
      );
      setChatSources(response.sources);
    } catch (error) {
      const message = getErrorMessage(error, 'Failed to submit question.');
      setChatError(message);
      throw error;
    } finally {
      setIsChatLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Private document RAG assistant</p>
          <h1>Ask questions across your uploaded documents</h1>
        </div>
        <p className="app-description">
          Upload PDFs, DOCX files, or spreadsheets, then ask questions with cited answers from the indexed
          content.
        </p>
      </header>

      <main className="app-grid">
        <div className="column-stack">
          <UploadPanel errorMessage={uploadError} isUploading={isUploading} onUpload={handleUpload} />

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Repository</p>
                <h2>Indexed documents</h2>
              </div>
            </div>

            {documentsError !== null ? <p className="error-message">{documentsError}</p> : null}
            {isDocumentsLoading ? <p className="muted-text">Loading document library...</p> : null}
            {!isDocumentsLoading && documents.length === 0 && documentsError === null ? (
              <p className="muted-text">No documents are indexed yet. Upload a file to begin.</p>
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