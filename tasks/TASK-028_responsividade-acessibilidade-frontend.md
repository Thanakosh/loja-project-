---
task_id: TASK-028
title: "Responsividade e acessibilidade do frontend"
status: pendente
priority: baixa
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Garantir que todas as telas do frontend funcionem bem em diferentes tamanhos de
tela (especialmente no app Electron em resoluções menores) e atendam padrões
mínimos de acessibilidade.

### Ações

1. **Responsividade:**
   - Auditar todas as 13 páginas para breakpoints menores (1024px, 768px).
   - Corrigir tabelas que quebram em telas menores (scroll horizontal ou layout
     alternativo em card).
   - Testar no Electron em janela redimensionada.

2. **Acessibilidade (a11y):**
   - Adicionar `aria-label` em botões de ícone.
   - Garantir contraste mínimo WCAG AA em modo claro e escuro.
   - Labels associados a todos os inputs (`htmlFor` / `id`).
   - Navegação por teclado funcional nos modais.

### Critério de aceite

- Todas as tabelas são utilizáveis em 1024px de largura.
- Lighthouse Accessibility score >= 85 na página principal.
