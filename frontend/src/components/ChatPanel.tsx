/**
 * Painel de chat para interação com o assistente RAG.
 *
 * Permite ao usuário digitar uma pergunta, enviá-la ao backend
 * e visualizar a resposta gerada pelo assistente. Também exibe
 * o escopo atual de busca (todo o repositório ou documento específico).
 */
import { FormEvent, useState } from 'react';

/** Propriedades aceitas pelo componente ChatPanel. */
interface ChatPanelProps {
  /** Resposta textual do assistente à pergunta atual. */
  answer: string;
  /** Mensagem de erro, ou null se não houver erro. */
  errorMessage: string | null;
  /** Indica se uma requisição de chat está em andamento. */
  isLoading: boolean;
  /** Rótulo descritivo do escopo de busca atual. */
  scopeLabel: string;
  /** Callback chamado quando o usuário envia uma pergunta. */
  onSubmit: (question: string) => Promise<void>;
}

/**
 * Componente de painel de chat.
 *
 * Gerencia o estado local da pergunta digitada e delega o envio
 * ao componente pai via callback onSubmit.
 */
export default function ChatPanel({
  answer,
  errorMessage,
  isLoading,
  scopeLabel,
  onSubmit
}: ChatPanelProps) {
  /** Estado local com o texto da pergunta digitada pelo usuário. */
  const [question, setQuestion] = useState<string>('');

  /**
   * Handler de envio do formulário de chat.
   * Valida a pergunta, chama o callback do pai e limpa o campo.
   *
   * @param event - Evento de submit do formulário
   */
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
      // O componente pai é responsável pelo estado de erro.
    }
  }

  return (
    <section className="panel chat-panel">
      {/* Cabeçalho com título e indicador de escopo */}
      <div className="panel-header">
        <div>
          <p className="eyebrow">Chat</p>
          <h2>Faça uma pergunta</h2>
        </div>
        <p className="scope-label">Scope: {scopeLabel}</p>
      </div>

      {/* Formulário de entrada da pergunta */}
      <form className="chat-form" onSubmit={handleSubmit}>
        <label className="field-label" htmlFor="question">
          Pergunta
        </label>
        <textarea
          id="question"
          className="textarea"
          rows={5}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Pergunte sobre os documentos carregados..."
        />

        <div className="actions-row">
          <button className="primary-button" type="submit" disabled={isLoading || question.trim().length === 0}>
            {isLoading ? 'Buscando..' : 'Faça uma pergunta'}
          </button>
        </div>
      </form>

      {/* Exibição de mensagem de erro, se houver */}
      {errorMessage !== null ? <p className="error-message">{errorMessage}</p> : null}

      {/* Card de exibição da resposta do assistente */}
      <div className="answer-card">
        <div className="answer-card-header">
          <h3>Resposta</h3>
        </div>
        {isLoading ? (
          <p className="muted-text">Buscando no repositório pelas respostas citadas, Isso pode demorar um pouco...</p>
        ) : answer.trim().length > 0 ? (
          <p className="answer-text">{answer}</p>
        ) : (
          <p className="muted-text">Sem respostas ainda. Faça uma pergunta para começar.</p>
        )}
      </div>
    </section>
  );
}

