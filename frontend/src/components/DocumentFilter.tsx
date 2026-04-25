import { DocumentSummary } from '../api/client';

interface DocumentFilterProps {
  documents: DocumentSummary[];
  isLoading: boolean;
  selectedDocumentId: string;
  onChange: (documentId: string) => void;
}

export default function DocumentFilter({
  documents,
  isLoading,
  selectedDocumentId,
  onChange
}: DocumentFilterProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Repository</p>
          <h2>Document filter</h2>
        </div>
      </div>

      <label className="field-label" htmlFor="document-filter">
        Search scope
      </label>
      <select
        id="document-filter"
        className="select"
        value={selectedDocumentId}
        onChange={(event) => onChange(event.target.value)}
        disabled={isLoading || documents.length === 0}
      >
        <option value="">All repository documents</option>
        {documents.map((document) => (
          <option key={document.id} value={document.id}>
            {document.filename} ({document.chunk_count} chunks)
          </option>
        ))}
      </select>

      {isLoading ? (
        <p className="muted-text">Loading available documents...</p>
      ) : documents.length === 0 ? (
        <p className="muted-text">Upload documents to limit answers to a single file.</p>
      ) : (
        <p className="muted-text">{documents.length} indexed document{documents.length === 1 ? '' : 's'} available.</p>
      )}
    </section>
  );
}