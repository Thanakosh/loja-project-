---
task_id: TASK-035
title: "Versionar package-lock.json no repositório"
status: pendente
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Garantir reprodutibilidade do build do frontend (especialmente no Electron)
removendo `package-lock.json` do `.gitignore` e versionando-o no repositório.

### Contexto

O `.gitignore` raiz (linha 38) ignora `package-lock.json`. Isso significa que
cada desenvolvedor ou agente que roda `npm install` pode obter versões
diferentes de dependências, causando builds irreproducíveis — particularmente
crítico para o build Electron (`electron-forge make`).

### Ações

1. Remover a linha `package-lock.json` do `.gitignore` raiz.
2. Verificar se existe `yarn.lock` (também ignorado) — se o projeto usar
   exclusivamente npm, manter `yarn.lock` no `.gitignore`.
3. Executar `npm install` no diretório `frontend/` para gerar o lockfile
   atualizado.
4. Adicionar `frontend/package-lock.json` ao Git:
   ```bash
   git add frontend/package-lock.json
   ```
5. Verificar que o build funciona corretamente:
   ```bash
   cd frontend && npm run build
   ```

### Critério de aceite

- `package-lock.json` está versionado no repositório.
- `.gitignore` não ignora mais `package-lock.json`.
- `npm ci` funciona corretamente no diretório `frontend/`.
- Build de produção (`npm run build`) executa sem erros.

### Branch sugerida

`fix/versionar-package-lock`
