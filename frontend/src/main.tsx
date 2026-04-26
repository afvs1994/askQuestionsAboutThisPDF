/**
 * Ponto de entrada da aplicação React.
 *
 * Responsável por inicializar o React no DOM e montar o componente
 * raiz (<App />) dentro do elemento HTML com id "root".
 *
 * É usado o React.StrictMode para ajudar a identificar potenciais
 * problemas durante o desenvolvimento (ex: efeitos colaterais de
 * componentes, APIs obsoletas, etc.).
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

/** Busca o elemento raiz no DOM onde a aplicação será renderizada. */
const rootElement = document.getElementById('root');

/** Lança erro caso o elemento raiz não exista (problema de configuração do HTML). */
if (rootElement === null) {
  throw new Error('Root element not found.');
}

/** Cria a raiz do React e renderiza o componente App dentro do StrictMode. */
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
