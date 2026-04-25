import { ChatSource } from '../api/client';

interface SourceListProps {
  sources: ChatSource[];
}

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

export default function SourceList({ sources }: SourceListProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Citations</p>
          <h2>Source list</h2>
        </div>
      </div>

      {sources.length === 0 ? (
        <p className="muted-text">Citations will appear here after you ask a question.</p>
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