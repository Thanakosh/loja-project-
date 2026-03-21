---
task_id: TASK-036
title: "Auditar historico Git por .env e credenciais commitadas"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Verificar se o arquivo `.env` ou qualquer credencial sensivel foi commitada
no historico do Git e, se necessario, remove-la do historico para evitar
vazamento de segredos.

### Contexto

O arquivo `.env` (2.5KB) esta presente no diretorio raiz do projeto. Embora
o `.gitignore` o exclua atualmente, e possivel que tenha sido commitado em
algum momento antes da regra de ignore ser adicionada.

### Acoes

1. **Verificar se `.env` esta no historico do Git:**
   ```bash
   git log --all --full-history -- .env
   git log --all --full-history -- "*.env"
   git log --all --full-history -- backend/.env
   ```
2. **Buscar por strings sensiveis no historico:**
   ```bash
   git log --all -p --diff-filter=A -- .env
   ```
3. **Se encontrar commits com `.env`:**
   - Documentar os commits afetados.
   - Avaliar se credenciais reais foram expostas.
   - Se sim, recomendar rotacao imediata de todas as chaves expostas
     (JWT_SECRET, DATABASE_URL password, tokens de WhatsApp, etc.).
   - Usar `git filter-branch` ou `git-filter-repo` para remover do historico
     (requer coordenacao com o time).
4. **Verificar tambem:**
   - `test.db` no historico.
   - `loja.db` no historico.
   - Qualquer arquivo com extensao `.key`, `.pem`, `.p12`.
5. **Gerar relatorio** com resultado da auditoria em `docs/auditoria-git-segredos.md`.

### Criterio de aceite

- Relatorio de auditoria gerado documentando se foram encontradas credenciais.
- Se foram encontradas: lista de acoes corretivas executadas ou recomendadas.
- Se nao foram encontradas: documento atesta que o historico esta limpo.

### Observacoes para o agente

 Esta tarefa e de **leitura e analise** - nao altere o historico do Git
sem aprovacao explicita do usuario. Apenas gere o relatorio e recomendacoes.

### Branch sugerida

`docs/auditoria-git-segredos`
