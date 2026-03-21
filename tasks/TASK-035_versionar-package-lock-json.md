---
task_id: TASK-035
title: "Versionar package-lock.json no repositArio"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Garantir reprodutibilidade do build do frontend (especialmente no Electron)
removendo `package-lock.json` do `.gitignore` e versionando-o no repositArio.

### Contexto

O `.gitignore` raiz (linha 38) ignora `package-lock.json`. Isso significa que
cada desenvolvedor ou agente que roda `npm install` pode obter versAes
diferentes de dependAncias, causando builds irreproducAveis a" particularmente
crAtico para o build Electron (`electron-forge make`).

### AAAes

1. Remover a linha `package-lock.json` do `.gitignore` raiz.
2. Verificar se existe `yarn.lock` (tambAm ignorado) a" se o projeto usar
   exclusivamente npm, manter `yarn.lock` no `.gitignore`.
3. Executar `npm install` no diretArio `frontend/` para gerar o lockfile
   atualizado.
4. Adicionar `frontend/package-lock.json` ao Git:
   ```bash
   git add frontend/package-lock.json
   ```
5. Verificar que o build funciona corretamente:
   ```bash
   cd frontend && npm run build
   ```

### CritArio de aceite

- `package-lock.json` estA versionado no repositArio.
- `.gitignore` nAo ignora mais `package-lock.json`.
- `npm ci` funciona corretamente no diretArio `frontend/`.
- Build de produAAo (`npm run build`) executa sem erros.

### Branch sugerida

`fix/versionar-package-lock`
