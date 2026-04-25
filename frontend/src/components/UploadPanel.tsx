import { ChangeEvent, FormEvent, useRef, useState } from 'react';

interface UploadPanelProps {
  errorMessage: string | null;
  isUploading: boolean;
  onUpload: (files: File[]) => Promise<void>;
}

export default function UploadPanel({ errorMessage, isUploading, onUpload }: UploadPanelProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>): void {
    const files = event.target.files;
    setSelectedFiles(files === null ? [] : Array.from(files));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (selectedFiles.length === 0 || isUploading) {
      return;
    }

    try {
      await onUpload(selectedFiles);
      setSelectedFiles([]);
      if (fileInputRef.current !== null) {
        fileInputRef.current.value = '';
      }
    } catch {
      // The parent component owns the error state.
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Ingest</p>
          <h2>Upload documents</h2>
        </div>
      </div>

      <form className="upload-form" onSubmit={handleSubmit}>
        <label className="field-label" htmlFor="documents">
          PDF, DOCX, or XLSX files
        </label>
        <input
          ref={fileInputRef}
          id="documents"
          className="file-input"
          type="file"
          accept=".pdf,.docx,.xlsx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          multiple
          onChange={handleFileChange}
        />

        {selectedFiles.length > 0 ? (
          <ul className="file-list">
            {selectedFiles.map((file) => (
              <li key={`${file.name}-${file.lastModified}`}>
                <span className="file-name">{file.name}</span>
                <span className="file-meta">{Math.ceil(file.size / 1024)} KB</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted-text">Choose one or more files to add them to the knowledge base.</p>
        )}

        <div className="actions-row">
          <button className="primary-button" type="submit" disabled={isUploading || selectedFiles.length === 0}>
            {isUploading ? 'Uploading...' : 'Upload files'}
          </button>
        </div>
      </form>

      {errorMessage !== null ? <p className="error-message">{errorMessage}</p> : null}
    </section>
  );
}