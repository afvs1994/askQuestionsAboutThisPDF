/**
 * Componente de filtro de documentos para limitar o escopo de busca.
 *
 * Permite ao usuário escolher entre pesquisar em todo o repositório
 * ou limitar a resposta a um único documento específico.
 * Esse controle é essencial para a precisão técnica exigida pelo
 * público-alvo (engenheiros e pesquisadores).
 */
import { DocumentSummary } from '../api/client';

/** Propriedades aceitas pelo componente DocumentFilter. */
interface DocumentFilterProps {
  /** Lista de documentos disponíveis para seleção. */
  documents: DocumentSummary[];
  /** Indica se a lista de documentos está sendo carregada. */
  isLoading: boolean;
  /** ID do documento atualmente selecionado (vazio = todos). */
  selectedDocumentId: string;
  /** Callback chamado quando o usuário muda a seleção. */
  onChange: (documentId: string) => void;
}

/**
 * Componente de filtro de documentos.
 *
 * Renderiza um dropdown (<select>) com a opção "All repository documents"
 * mais uma entrada para cada documento indexado. Inclui mensagens
 * informativas sobre o estado atual (carregando, vazio, etc.).
 */
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
          <p className="eyebrow">Repositório</p>
          <h2>Filtro de documentos</h2>
        </div>
      </div>

      {/* Label e dropdown de seleção de escopo */}
      <label className="field-label" htmlFor="document-filter">
        Procure o escopo
      </label>
      <select
        id="document-filter"
        className="select"
        value={selectedDocumentId}
        onChange={(event) => onChange(event.target.value)}
        disabled={isLoading || documents.length === 0}
      >
        <option value="">Todos os documentos do repositório</option>
        {documents.map((document) => (
          <option key={document.id} value={document.id}>
            {document.filename} ({document.chunk_count} chunks)
          </option>
        ))}
      </select>

      {/* Mensagem informativa sobre o estado atual */}
      {isLoading ? (
        <p className="muted-text">Carregando documentos disponíveis...</p>
      ) : documents.length === 0 ? (
        <p className="muted-text">Carregue documentos para limitar respostas a um único arquivo.</p>
      ) : (
        <p className="muted-text">{documents.length} indexados documento{documents.length === 1 ? '' : 's'} disponíve{documents.length === 1 ? 'l' : 'is'}.</p>
      )}
    </section>
  );
}

