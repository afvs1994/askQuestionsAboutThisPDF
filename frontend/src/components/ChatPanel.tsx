import { FormEvent, useState } from 'react';

interface ChatPanelProps {
  answer: string;
  errorMessage: string | null;
  isLoading: boolean;
  scopeLabel: string;
  onSubmit: (question: string) => Promise<void>;
}

export default function ChatPanel({
  answer,
  errorMessage,
  isLoading,
  scopeLabel,
  onSubmit
}: ChatPanelProps) {
  const [question, setQuestion] = useState<string>('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const trimmedQuestion = question.trim();
    if (trimmedQuestion.length === 0 || isLoading) {
      return;
    }

    try {
      await onSubmit(trimmedQuestion);
      setQuestion('');
    } catch {
      // The parent component owns the error state.
    }
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Chat</p>
          <h2>Ask a question</h2>
        </div>
        <p className="scope-label">Scope: {scopeLabel}</p>
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <label className="field-label" htmlFor="question">
          Question
        </label>
        <textarea
          id="question"
          className="textarea"
          rows={5}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about the uploaded documents..."
        />

        <div className="actions-row">
          <button className="primary-button" type="submit" disabled={isLoading || question.trim().length === 0}>
            {isLoading ? 'Searching...' : 'Ask question'}
          </button>
        </div>
      </form>

      {errorMessage !== null ? <p className="error-message">{errorMessage}</p> : null}

      <div className="answer-card">
        <div className="answer-card-header">
          <h3>Answer</h3>
        </div>
        {isLoading ? (
          <p className="muted-text">Searching the repository for cited answers...</p>
        ) : answer.trim().length > 0 ? (
          <p className="answer-text">{answer}</p>
        ) : (
          <p className="muted-text">No answer yet. Ask a question to get started.</p>
        )}
      </div>
    </section>
  );
}