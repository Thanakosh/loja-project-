---
task_id: TASK-020
title: "Atualizar checklist de telas do frontend no RECOMENDACOES_TECNICAS.md"
status: concluida
priority: baixa
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

A secao " Frontend (Telas Planejadas)" no `RECOMENDACOES_TECNICAS.md` ainda marca
todas as telas como `[ ]`, porem ja existem **13 paginas** implementadas:

Login, Dashboard, PDV, Produtos, Estoque, Orcamentos, Vendas, Fornecedores,
Clientes, ContasReceber, Relatorios, NotasFiscais, ImportarNota.

### Acoes

1. Marcar como `[x]` todas as telas que ja possuem componente funcional em
   `frontend/src/pages/`.
2. Adicionar telas novas ainda nao listadas (Contas a Receber, Notas Fiscais,
   Importar Nota).
3. Identificar melhorias pendentes por tela (ex.: responsividade, acessibilidade).

### Criterio de aceite

- Checklist reflete a realidade do codigo em `frontend/src/pages/`.
