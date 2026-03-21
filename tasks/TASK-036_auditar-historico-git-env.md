---
task_id: TASK-036
title: "Auditar histórico Git por .env e credenciais commitadas"
status: pendente
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Verificar se o arquivo `.env` ou qualquer credencial sensível foi commitada
no histórico do Git e, se necessário, removê-la do histórico para evitar
vazamento de segredos.

### Contexto

O arquivo `.env` (2.5KB) está presente no diretório raiz do projeto. Embora
o `.gitignore` o exclua atualmente, é possível que tenha sido commitado em
algum momento antes da regra de ignore ser adicionada.

### Ações

1. **Verificar se `.env` está no histórico do Git:**
   ```bash
   git log --all --full-history -- .env
   git log --all --full-history -- "*.env"
   git log --all --full-history -- backend/.env
   ```
2. **Buscar por strings sensíveis no histórico:**
   ```bash
   git log --all -p --diff-filter=A -- .env
   ```
3. **Se encontrar commits com `.env`:**
   - Documentar os commits afetados.
   - Avaliar se credenciais reais foram expostas.
   - Se sim, recomendar rotação imediata de todas as chaves expostas
     (JWT_SECRET, DATABASE_URL password, tokens de WhatsApp, etc.).
   - Usar `git filter-branch` ou `git-filter-repo` para remover do histórico
     (requer coordenação com o time).
4. **Verificar também:**
   - `test.db` no histórico.
   - `loja.db` no histórico.
   - Qualquer arquivo com extensão `.key`, `.pem`, `.p12`.
5. **Gerar relatório** com resultado da auditoria em `docs/auditoria-git-segredos.md`.

### Critério de aceite

- Relatório de auditoria gerado documentando se foram encontradas credenciais.
- Se foram encontradas: lista de ações corretivas executadas ou recomendadas.
- Se não foram encontradas: documento atesta que o histórico está limpo.

### Observações para o agente

⚠️ Esta tarefa é de **leitura e análise** — não altere o histórico do Git
sem aprovação explícita do usuário. Apenas gere o relatório e recomendações.

### Branch sugerida

`docs/auditoria-git-segredos`
