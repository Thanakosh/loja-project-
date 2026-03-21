---
task_id: TASK-038
title: "Refatorar páginas grandes do frontend em componentes reutilizáveis"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-034"]
---

## Objetivo

Decompor as 5 maiores páginas do frontend em componentes reutilizáveis para
melhorar manutenção, testabilidade e consistência visual.

### Contexto

As seguintes páginas são monolíticas e excedem 38KB cada:

| Página | Tamanho | Prioridade de refatoração |
|--------|---------|--------------------------|
| `ImportarNota.tsx` | 57KB | 🔴 Alta |
| `PDV.tsx` | 46KB | 🔴 Alta |
| `Produtos.tsx` | 41KB | 🟡 Média |
| `Relatorios.tsx` | 41KB | 🟡 Média |
| `Orcamentos.tsx` | 38KB | 🟡 Média |

Atualmente o diretório `frontend/src/components/` possui apenas 2 componentes
compartilhados: `Layout.tsx` e `PrivateRoute.tsx`.

### Ações

#### Fase 1 — Componentes genéricos reutilizáveis

Criar em `frontend/src/components/ui/`:

1. **`DataTable.tsx`** — Tabela genérica com:
   - Paginação integrada
   - Ordenação por coluna
   - Loading state / empty state
   - Props tipadas para colunas e dados
2. **`Modal.tsx`** — Modal genérico com:
   - Overlay, animação de entrada/saída
   - Tamanhos configuráveis (sm, md, lg, xl)
   - Suporte a acessibilidade (focus trap, aria)
3. **`SearchFilter.tsx`** — Barra de busca/filtro reutilizável
4. **`ConfirmDialog.tsx`** — Dialog de confirmação para ações destrutivas
5. **`StatusBadge.tsx`** — Badges de status padronizados
6. **`PageHeader.tsx`** — Header de página com título e ações

#### Fase 2 — Decomposição das páginas (começar por PDV.tsx e ImportarNota.tsx)

Para cada página, extrair:
- **Formulários** em componentes próprios (ex: `ProdutoForm.tsx`)
- **Modais** específicos do domínio (ex: `VendaModal.tsx`)
- **Seções** lógicas (ex: `PDVItemList.tsx`, `PDVSummary.tsx`, `PDVActions.tsx`)

#### Estrutura de diretórios sugerida

```
frontend/src/components/
├── ui/           # Componentes genéricos
│   ├── DataTable.tsx
│   ├── Modal.tsx
│   ├── SearchFilter.tsx
│   ├── ConfirmDialog.tsx
│   ├── StatusBadge.tsx
│   └── PageHeader.tsx
├── pdv/          # Componentes do PDV
│   ├── PDVItemList.tsx
│   ├── PDVSummary.tsx
│   └── PDVPayment.tsx
├── produtos/     # Componentes de Produtos
│   ├── ProdutoForm.tsx
│   ├── ProdutoTable.tsx
│   └── CategoriaTreeSelect.tsx
└── ...
```

### Regras para o agente

- **Não alterar comportamento** — apenas extrair sem modificar lógica.
- **Manter tipagem TypeScript** — todas as props devem ser tipadas.
- **Um componente extraído por commit** para facilitar revisão.
- Seguir padrão TailwindCSS existente no projeto.
- **Não duplicar regras de negócio** no frontend (regra do AGENTS.md).

### Critério de aceite

- Pelo menos 6 componentes genéricos criados em `components/ui/`.
- `PDV.tsx` reduzido para < 15KB.
- `ImportarNota.tsx` reduzido para < 20KB.
- Todos os testes E2E existentes (se houver) continuam passando.
- Build (`npm run build`) sem erros.

### Branch sugerida

`frontend/refatorar-componentes-reutilizaveis`
