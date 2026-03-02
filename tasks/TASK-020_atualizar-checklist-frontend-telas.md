---
task_id: TASK-020
title: "Atualizar checklist de telas do frontend no RECOMENDACOES_TECNICAS.md"
status: concluída
priority: baixa
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

A seção "🖥️ Frontend (Telas Planejadas)" no `RECOMENDACOES_TECNICAS.md` ainda marca
todas as telas como `[ ]`, porém já existem **13 páginas** implementadas:

Login, Dashboard, PDV, Produtos, Estoque, Orçamentos, Vendas, Fornecedores,
Clientes, ContasReceber, Relatórios, NotasFiscais, ImportarNota.

### Ações

1. Marcar como `[x]` todas as telas que já possuem componente funcional em
   `frontend/src/pages/`.
2. Adicionar telas novas ainda não listadas (Contas a Receber, Notas Fiscais,
   Importar Nota).
3. Identificar melhorias pendentes por tela (ex.: responsividade, acessibilidade).

### Critério de aceite

- Checklist reflete a realidade do código em `frontend/src/pages/`.
