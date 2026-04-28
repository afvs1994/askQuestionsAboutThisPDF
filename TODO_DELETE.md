# TODO - Implementação de Deleção de Documentos

## Backend
- [x] `backend/app/core/storage.py` - Adicionar método `delete_document()`
- [x] `backend/app/services/vector_store.py` - Adicionar método `delete_by_document_id()`
- [x] `backend/app/services/rag.py` - Adicionar método `delete_document()`
- [x] `backend/app/api/documents.py` - Adicionar endpoint DELETE /{document_id}

## Frontend
- [x] `frontend/src/api/client.ts` - Adicionar função `deleteDocument()`
- [x] `frontend/src/App.tsx` - Adicionar botão de delete, confirmação e handler
- [x] `frontend/src/styles.css` - Adicionar estilos para botão de delete

## Testes
- [ ] Testar backend (pytest)
- [ ] Testar build do frontend
- [ ] Verificar que não há regressões

