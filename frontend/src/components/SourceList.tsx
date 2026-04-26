/**
 * Componente de exibição das fontes/citações das respostas do assistente.
 *
 * Mostra os trechos dos documentos que foram recuperados pelo sistema RAG
 * e usados como contexto para gerar a resposta. Cada fonte inclui:
 * - Localização (página, planilha, chunk)
 * - Score de similaridade
 * - Trecho do texto original
 *
 * Isso permite ao usuário verificar a proveniência da informação,
 * reduzindo alucinações e aumentando a confiança na resposta.
 */
import { ChatSource } from '../api/client';

/** Propriedades aceitas pelo componente SourceList. */
interface SourceListProps {
  /** Lista de fontes retornadas pelo backend para a última pergunta. */
  sources: ChatSource[];
}

/**
 * Formata a localização de uma fonte em partes legíveis.
 * Combina nome do arquivo, página, planilha e número do chunk.
 *
 * @param source - Fonte de citação
 * @returns Array de strings com as partes da localização
 */
function formatLocation(source: ChatSource): string[] {
  const locationParts: string[] = [];

  if (source.filename !== undefined && source.filename.trim().length > 0) {
    locationParts.push(source.filename);
  }

  if (source.page !== undefined) {
    locationParts.push(`Page ${source.page}`);
  }

  if (source.sheet !== undefined && source.sheet.trim().length > 0) {
    locationParts.push(`Sheet ${source.sheet}`);
  }

  if (source.chunk !== undefined) {
    locationParts.push(`Chunk ${source.chunk}`);
  }

  return locationParts;
}

/**
 * Componente de lista de fontes/citações.
 *
 * Renderiza uma lista ordenada (ol) com cards para cada fonte
 * recuperada pelo RAG. Inclui informações de localização e score.
 */
export default function SourceList({ sources }: SourceListProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Citações</p>
          <h2>Lista de fontes</h2>
        </div>
      </div>

      {/* Estado vazio: nenhuma pergunta foi feita ainda */}
      {sources.length === 0 ? (
        <p className="muted-text">Citações aparecerão aqui após formulada a pergunta.</p>
      ) : (
        <ol className="source-list">
          {sources.map((source, index) => {
            const locationParts = formatLocation(source);

            return (
              <li className="source-card" key={`${index}-${source.excerpt.slice(0, 24)}`}>
                <div className="source-card-header">
                  <span className="source-index">Source {index + 1}</span>
                  <span className="score-pill">Score {source.score.toFixed(4)}</span>
                </div>

                {locationParts.length > 0 ? <p className="source-location">{locationParts.join(' · ')}</p> : null}
                <p className="source-excerpt">{source.excerpt}</p>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}

