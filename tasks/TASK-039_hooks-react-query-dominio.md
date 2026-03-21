---
task_id: TASK-039
title: "Criar hooks React Query por dominio"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-034"]
---

## Objetivo

Criar custom hooks com React Query (`@tanstack/react-query`) para cada modulo
de negocio, centralizando logica de fetch, cache, invalidacao e mutacoes.

### Contexto

O projeto ja tem `@tanstack/react-query` como dependencia, mas a comunicacao
com o backend esta concentrada em `frontend/src/services/api.ts` (~3KB) com
chamadas diretas. As 15 paginas fazem chamadas `apiClient.get/post` diretamente,
sem cache ou estado compartilhado - cada navegacao refaz todas as chamadas.

### Acoes

Criar em `frontend/src/hooks/` um arquivo por dominio:

1. **`useProdutos.ts`** - queries e mutations para produtos:
   - `useProdutos(filtros)` - listagem com paginacao
   - `useProduto(id)` - detalhes
   - `useCreateProduto()` - mutation de criacao
   - `useUpdateProduto()` - mutation de edicao
   - Invalidation automatica apos mutacoes

2. **`useEstoque.ts`** - queries para estoque:
   - `useEstoqueCompleto(filtros)` - listagem
   - `useEstoqueProduto(id)` - estoque de um produto
   - `useRegistrarTransacao()` - mutation

3. **`useVendas.ts`** - queries para vendas e PDV:
   - `useVendas(filtros)` - listagem
   - `useRegistrarVenda()` - mutation do PDV
   - `useCancelarVenda()` - mutation

4. **`useClientes.ts`** - queries para clientes
5. **`useFornecedores.ts`** - queries para fornecedores
6. **`useOrcamentos.ts`** - queries para orcamentos
7. **`useCaixa.ts`** - queries para caixa diario
8. **`useContasReceber.ts`** - queries para contas a receber

### Padrao a seguir

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
- **Nao alterar a API de backend** - apenas consumir o que ja existe.
- **Manter compatibilidade** - paginas existentes devem continuar funcionando.
- Migrar as paginas gradualmente: comecar por `Dashboard.tsx` (mais simples)
  e `Produtos.tsx` como prova de conceito.
- Configurar `staleTime` adequado (ex: 30s para listagens, 5min para dados estaticos).

### Criterio de aceite

- Pelo menos 8 hooks criados cobrindo todos os dominios principais.
- `Dashboard.tsx` e `Produtos.tsx` migrados para usar os hooks.
- Cache funcionando (navegar/voltar nao refaz fetch desnecessario).
- Nenhum erro de TypeScript.
- Build sem erros.

### Branch sugerida

`frontend/react-query-hooks`

### Execucao realizada

- hooks criados em `frontend/src/hooks/` para produtos, estoque, vendas,
  clientes, fornecedores, orcamentos, caixa e contas a receber
- hook adicional `useDashboard.ts` criado para o card fiscal
- tipos compartilhados extraidos para `frontend/src/types/`
- `Dashboard.tsx` migrado para consumir hooks de vendas, orcamentos, produtos,
  estoque e fiscal
- `Produtos.tsx` migrado para consumir hooks de listagem, categorias,
  duplicidade e mutacoes
- validacao executada com `eslint` nos arquivos tocados e `vite build`
