---
task_id: TASK-028
title: "Responsividade e acessibilidade do frontend"
status: concluida
priority: baixa
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Garantir que todas as telas do frontend funcionem bem em diferentes tamanhos de
tela (especialmente no app Electron em resolucoes menores) e atendam padroes
minimos de acessibilidade.

### Acoes

1. **Responsividade:**
   - Auditar todas as 13 paginas para breakpoints menores (1024px, 768px).
   - Corrigir tabelas que quebram em telas menores (scroll horizontal ou layout
     alternativo em card).
   - Testar no Electron em janela redimensionada.

2. **Acessibilidade (a11y):**
   - Adicionar `aria-label` em botoes de icone.
   - Garantir contraste minimo WCAG AA em modo claro e escuro.
   - Labels associados a todos os inputs (`htmlFor` / `id`).
   - Navegacao por teclado funcional nos modais.

### Criterio de aceite

- Todas as tabelas sao utilizaveis em 1024px de largura.
- Lighthouse Accessibility score >= 85 na pagina principal.

## Entregue

- Ajustes de responsividade em tabelas e paginacao das telas de produtos,
  orcamentos, estoque, notas fiscais e fornecedores.
- `aria-label` adicionados em botoes de icone e acoes sem texto suficiente.
- Navegacao por teclado e fechamento por `Escape` nos modais principais via
  `useAccessibleModal`.
- Associacao de `label` e `id` nos formularios/modais tocados nesta etapa.

## Validacao

- Auditoria real em viewport de `1024px` nas telas principais sem overflow
  horizontal global.
- `npm run test:e2e`: 5 testes aprovados.
- `node .\\node_modules\\vite\\bin\\vite.js build`: ok.
- Lighthouse Accessibility: `97` no build local da pagina principal.
