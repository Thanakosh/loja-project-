---
task_id: TASK-038
title: "Refatorar paginas grandes do frontend em componentes reutilizaveis"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-034"]
---

## Objetivo

Decompor as 5 maiores paginas do frontend em componentes reutilizaveis para
melhorar manutencao, testabilidade e consistencia visual.

### Contexto

As seguintes paginas sao monoliticas e excedem 38KB cada:

| Pagina | Tamanho | Prioridade de refatoracao |
|--------|---------|--------------------------|
| `ImportarNota.tsx` | 57KB |  Alta |
| `PDV.tsx` | 46KB |  Alta |
| `Produtos.tsx` | 41KB |  Media |
| `Relatorios.tsx` | 41KB |  Media |
| `Orcamentos.tsx` | 38KB |  Media |

Atualmente o diretorio `frontend/src/components/` possui apenas 2 componentes
compartilhados: `Layout.tsx` e `PrivateRoute.tsx`.

### Acoes

#### Fase 1 - Componentes genericos reutilizaveis

Criar em `frontend/src/components/ui/`:

1. **`DataTable.tsx`** - Tabela generica com:
   - Paginacao integrada
   - Ordenacao por coluna
   - Loading state / empty state
   - Props tipadas para colunas e dados
2. **`Modal.tsx`** - Modal generico com:
   - Overlay, animacao de entrada/saida
   - Tamanhos configuraveis (sm, md, lg, xl)
   - Suporte a acessibilidade (focus trap, aria)
3. **`SearchFilter.tsx`** - Barra de busca/filtro reutilizavel
4. **`ConfirmDialog.tsx`** - Dialog de confirmacao para acoes destrutivas
5. **`StatusBadge.tsx`** - Badges de status padronizados
6. **`PageHeader.tsx`** - Header de pagina com titulo e acoes

#### Fase 2 - Decomposicao das paginas (comecar por PDV.tsx e ImportarNota.tsx)

Para cada pagina, extrair:
- **Formularios** em componentes proprios (ex: `ProdutoForm.tsx`)
- **Modais** especificos do dominio (ex: `VendaModal.tsx`)
- **Secoes** logicas (ex: `PDVItemList.tsx`, `PDVSummary.tsx`, `PDVActions.tsx`)

#### Estrutura de diretorios sugerida

```
frontend/src/components/
 ui/           # Componentes genericos
    DataTable.tsx
    Modal.tsx
    SearchFilter.tsx
    ConfirmDialog.tsx
    StatusBadge.tsx
    PageHeader.tsx
 pdv/          # Componentes do PDV
    PDVItemList.tsx
    PDVSummary.tsx
    PDVPayment.tsx
 produtos/     # Componentes de Produtos
    ProdutoForm.tsx
    ProdutoTable.tsx
    CategoriaTreeSelect.tsx
 ...
```

### Regras para o agente

- **Nao alterar comportamento** - apenas extrair sem modificar logica.
- **Manter tipagem TypeScript** - todas as props devem ser tipadas.
- **Um componente extraido por commit** para facilitar revisao.
- Seguir padrao TailwindCSS existente no projeto.
- **Nao duplicar regras de negocio** no frontend (regra do AGENTS.md).

### Criterio de aceite

- Pelo menos 6 componentes genericos criados em `components/ui/`.
- `PDV.tsx` reduzido para < 15KB.
- `ImportarNota.tsx` reduzido para < 20KB.
- Todos os testes E2E existentes (se houver) continuam passando.
- Build (`npm run build`) sem erros.

### Branch sugerida

`frontend/refatorar-componentes-reutilizaveis`
