---
task_id: TASK-039
title: "Criar hooks React Query por domínio"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-034"]
---

## Objetivo

Criar custom hooks com React Query (`@tanstack/react-query`) para cada módulo
de negócio, centralizando lógica de fetch, cache, invalidação e mutações.

### Contexto

O projeto já tem `@tanstack/react-query` como dependência, mas a comunicação
com o backend está concentrada em `frontend/src/services/api.ts` (~3KB) com
chamadas diretas. As 15 páginas fazem chamadas `apiClient.get/post` diretamente,
sem cache ou estado compartilhado — cada navegação refaz todas as chamadas.

### Ações

Criar em `frontend/src/hooks/` um arquivo por domínio:

1. **`useProdutos.ts`** — queries e mutations para produtos:
   - `useProdutos(filtros)` — listagem com paginação
   - `useProduto(id)` — detalhes
   - `useCreateProduto()` — mutation de criação
   - `useUpdateProduto()` — mutation de edição
   - Invalidation automática após mutações

2. **`useEstoque.ts`** — queries para estoque:
   - `useEstoqueCompleto(filtros)` — listagem
   - `useEstoqueProduto(id)` — estoque de um produto
   - `useRegistrarTransacao()` — mutation

3. **`useVendas.ts`** — queries para vendas e PDV:
   - `useVendas(filtros)` — listagem
   - `useRegistrarVenda()` — mutation do PDV
   - `useCancelarVenda()` — mutation

4. **`useClientes.ts`** — queries para clientes
5. **`useFornecedores.ts`** — queries para fornecedores
6. **`useOrcamentos.ts`** — queries para orçamentos
7. **`useCaixa.ts`** — queries para caixa diário
8. **`useContasReceber.ts`** — queries para contas a receber

### Padrão a seguir

```typescript
// Exemplo: useProdutos.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'

export function useProdutos(page = 1, search = '') {
  return useQuery({
    queryKey: ['produtos', { page, search }],
    queryFn: () => apiClient.get('/api/v1/produtos/', { params: { skip: (page-1)*20, limit: 20, search } }).then(r => r.data),
  })
}

export function useCreateProduto() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProdutoCreate) => apiClient.post('/api/v1/produtos/', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['produtos'] }),
  })
}
```

### Regras para o agente

- **Tipar todas as respostas** com interfaces TypeScript (usar tipos de `frontend/src/types/`).
- **Não alterar a API de backend** — apenas consumir o que já existe.
- **Manter compatibilidade** — páginas existentes devem continuar funcionando.
- Migrar as páginas gradualmente: começar por `Dashboard.tsx` (mais simples)
  e `Produtos.tsx` como prova de conceito.
- Configurar `staleTime` adequado (ex: 30s para listagens, 5min para dados estáticos).

### Critério de aceite

- Pelo menos 8 hooks criados cobrindo todos os domínios principais.
- `Dashboard.tsx` e `Produtos.tsx` migrados para usar os hooks.
- Cache funcionando (navegar/voltar não refaz fetch desnecessário).
- Nenhum erro de TypeScript.
- Build sem erros.

### Branch sugerida

`frontend/react-query-hooks`
