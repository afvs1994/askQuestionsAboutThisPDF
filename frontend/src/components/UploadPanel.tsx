/**
 * Painel de upload de documentos para ingestão na base de conhecimento.
 *
 * Permite ao usuário selecionar um ou mais arquivos (PDF, DOCX, XLSX)
 * e enviá-los ao backend para processamento, chunking e indexação.
 * Exibe a lista de arquivos selecionados com seus tamanhos.
 */
import { ChangeEvent, FormEvent, useRef, useState } from 'react';

/** Propriedades aceitas pelo componente UploadPanel. */
interface UploadPanelProps {
  /** Mensagem de erro do upload, ou null se não houver erro. */
  errorMessage: string | null;
  /** Indica se um upload está em andamento. */
  isUploading: boolean;
  /** Callback chamado quando o usuário confirma o upload. */
  onUpload: (files: File[]) => Promise<void>;
}

/**
 * Componente de painel de upload.
 *
 * Gerencia o estado local dos arquivos selecionados e delega
 * o envio ao componente pai via callback onUpload.
 */
export default function UploadPanel({ errorMessage, isUploading, onUpload }: UploadPanelProps) {
  /** Lista de arquivos atualmente selecionados pelo usuário. */
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  /** Referência ao input de arquivo para permitir limpar o campo após upload. */
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  /**
   * Handler de mudança no input de arquivo.
   * Atualiza o estado com os arquivos selecionados.
   *
   * @param event - Evento de change do input file
   */
  function handleFileChange(event: ChangeEvent<HTMLInputElement>): void {
    const files = event.target.files;
    setSelectedFiles(files === null ? [] : Array.from(files));
  }

  /**
   * Handler de envio do formulário de upload.
   * Valida a seleção, chama o callback do pai e limpa o estado.
   *
   * @param event - Evento de submit do formulário
   */
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
      // O componente pai é responsável pelo estado de erro.
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Carregador</p>
          <h2>Documentos carregados</h2>
        </div>
      </div>

      {/* Formulário de upload com input de arquivo */}
      <form className="upload-form" onSubmit={handleSubmit}>
        <label className="field-label" htmlFor="documents">
          Arquivos PDF ou DOCX
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

        {/* Lista de arquivos selecionados ou mensagem informativa */}
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
          <p className="muted-text">Escolha um ou mais arquivos para adicionar à base de conhecimento.</p>
        )}

        <div className="actions-row">
          <button className="primary-button" type="submit" disabled={isUploading || selectedFiles.length === 0}>
            {isUploading ? 'Carregando..' : 'Carregue arquivos'}
          </button>
        </div>
      </form>

      {/* Exibição de mensagem de erro, se houver */}
      {errorMessage !== null ? <p className="error-message">{errorMessage}</p> : null}
    </section>
  );
}

