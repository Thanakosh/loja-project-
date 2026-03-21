---
task_id: TASK-034
title: "Extrair VITE_API_URL do hardcode no frontend"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Eliminar as URLs de backend hardcoded no frontend (`http://localhost:8000`),
substituindo por variavel de ambiente Vite para permitir deploy em diferentes
ambientes (dev, staging, producao).

### Contexto

Atualmente, `frontend/src/api/client.ts` contem a base URL do backend
hardcoded em dois lugares:
- Linha 6: `baseURL: 'http://localhost:8000'`
- Linha 71: `await axios.post('http://localhost:8000/api/v1/users/refresh', ...)`

Isso impede que o frontend funcione em ambientes que nao sejam localhost.

### Acoes

1. Criar arquivo `frontend/.env.example` com:
   ```
   VITE_API_URL=http://localhost:8000
   ```
2. Criar arquivo `frontend/.env` local (nao versionado) com o mesmo valor.
3. Refatorar `frontend/src/api/client.ts`:
   - Extrair constante: `const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`
   - Usar `API_BASE_URL` em `axios.create({ baseURL: API_BASE_URL })`.
   - Usar `API_BASE_URL` na chamada de refresh token (linha 71).
4. Verificar se existem outros arquivos com URLs hardcoded:
   - Buscar por `localhost:8000` em todo o diretorio `frontend/src/`.
   - Substituir todas as ocorrencias.
5. Adicionar `frontend/.env` ao `.gitignore` (se nao ja coberto pelo padrao `.env` raiz).
6. Atualizar `frontend/README.md` com instrucoes de configuracao da variavel.

### Criterio de aceite

- Nenhuma ocorrencia de `localhost:8000` hardcoded no codigo-fonte do frontend.
- Frontend funciona normalmente com `VITE_API_URL` configurado via `.env`.
- `frontend/.env.example` versionado como referencia.
- Build (`npm run build`) funciona sem erros.

### Branch sugerida

`fix/vite-api-url-env`
