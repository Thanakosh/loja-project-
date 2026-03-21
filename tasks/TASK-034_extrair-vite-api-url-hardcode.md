---
task_id: TASK-034
title: "Extrair VITE_API_URL do hardcode no frontend"
status: concluída
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Eliminar as URLs de backend hardcoded no frontend (`http://localhost:8000`),
substituindo por variável de ambiente Vite para permitir deploy em diferentes
ambientes (dev, staging, produção).

### Contexto

Atualmente, `frontend/src/api/client.ts` contém a base URL do backend
hardcoded em dois lugares:
- Linha 6: `baseURL: 'http://localhost:8000'`
- Linha 71: `await axios.post('http://localhost:8000/api/v1/users/refresh', ...)`

Isso impede que o frontend funcione em ambientes que não sejam localhost.

### Ações

1. Criar arquivo `frontend/.env.example` com:
   ```
   VITE_API_URL=http://localhost:8000
   ```
2. Criar arquivo `frontend/.env` local (não versionado) com o mesmo valor.
3. Refatorar `frontend/src/api/client.ts`:
   - Extrair constante: `const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`
   - Usar `API_BASE_URL` em `axios.create({ baseURL: API_BASE_URL })`.
   - Usar `API_BASE_URL` na chamada de refresh token (linha 71).
4. Verificar se existem outros arquivos com URLs hardcoded:
   - Buscar por `localhost:8000` em todo o diretório `frontend/src/`.
   - Substituir todas as ocorrências.
5. Adicionar `frontend/.env` ao `.gitignore` (se não já coberto pelo padrão `.env` raiz).
6. Atualizar `frontend/README.md` com instruções de configuração da variável.

### Critério de aceite

- Nenhuma ocorrência de `localhost:8000` hardcoded no código-fonte do frontend.
- Frontend funciona normalmente com `VITE_API_URL` configurado via `.env`.
- `frontend/.env.example` versionado como referência.
- Build (`npm run build`) funciona sem erros.

### Branch sugerida

`fix/vite-api-url-env`
