---
task_id: TASK-043
title: "Implementar design system com componentes reutilizaveis (Shadcn/ui)"
status: pendente
priority: baixa
agent_chat_executable: "sim"
depends_on: ["TASK-038"]
---

## Objetivo

Adotar uma biblioteca de componentes UI (Shadcn/ui recomendado) para
estabelecer um design system consistente no frontend, substituindo
componentes ad-hoc por uma base padronizada.

### Contexto

O frontend usa TailwindCSS para estilizacao, mas nao tem uma biblioteca de
componentes estruturada. Cada pagina implementa seus proprios botoes, inputs,
tabelas e modais com classes Tailwind avulsas, resultando em inconsistencia
visual e duplicacao de codigo. O AGENTS.md recomenda Shadcn/ui.

### Pre-requisitos

- TASK-038 concluida (componentes genericos extraidos, facilitando substituicao).
- TailwindCSS 3.4+ ja instalado e configurado.

### Acoes

#### Fase 1 - Setup do Shadcn/ui

1. **Inicializar Shadcn/ui no projeto:**
   ```bash
   cd frontend
   npx shadcn@latest init
   ```
   - Configurar `tailwind.config.js` conforme requerido.
   - Aceitar as defaults para `components.json`.

2. **Instalar componentes essenciais:**
   ```bash
   npx shadcn@latest add button input label select dialog table
   npx shadcn@latest add card badge alert separator
   npx shadcn@latest add dropdown-menu sheet toast tabs
   npx shadcn@latest add form popover command calendar
   ```

3. **Configurar tema (cores) do design system:**
   - Definir paleta de cores no `globals.css` alinhada com identidade do projeto.
   - Modo dark: avaliar se necessario nesta fase.

#### Fase 2 - Migracao gradual das paginas

Substituir componentes ad-hoc pelos componentes Shadcn:

| Componente atual (ad-hoc) | Substituto Shadcn |
|--------------------------|-------------------|
| `<button className="...">` | `<Button>` |
| `<input className="...">` | `<Input>` |
| `<table className="...">` | `<Table>` + `DataTable` |
| Modais customizados | `<Dialog>` |
| Selects customizados | `<Select>` / `<Command>` |
| Badges de status | `<Badge>` |
| Toast notifications | `<Toast>` (integrar com react-hot-toast ou substituir) |

**Ordem de migracao sugerida:**
1. `Login.tsx` (mais simples, prova de conceito)
2. `Dashboard.tsx`
3. `Produtos.tsx`
4. `PDV.tsx`
5. Demais paginas

#### Fase 3 - Documentacao

1. Criar `docs/design-system.md` com:
   - Lista de componentes Shadcn instalados.
   - Paleta de cores e tokens.
   - Padroes de uso (quando usar Dialog vs Sheet, etc.).
2. Atualizar `frontend/README.md` com instrucoes de adicao de novos componentes.

### Regras para o agente

- **Migrar uma pagina por PR** para facilitar revisao.
- **Manter funcionalidade** - apenas substituir visual, nao alterar logica.
- **Nao remover react-hot-toast** sem confirmar que o Toast do Shadcn cobre
  todos os casos de uso existentes.
- Seguir convencoes de import do Shadcn (`@/components/ui/button`).
- Configurar path alias `@/` no `tsconfig.json` e `vite.config.ts` se necessario.

### Criterio de aceite

- Shadcn/ui inicializado e configurado no projeto.
- Pelo menos 10 componentes Shadcn instalados.
- `Login.tsx` e `Dashboard.tsx` migrados para componentes Shadcn.
- Build sem erros.
- Visual consistente entre as paginas migradas.

### Branch sugerida

`frontend/shadcn-design-system`
