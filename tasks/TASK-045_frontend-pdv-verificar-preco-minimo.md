---
task_id: TASK-045
title: "Frontend: verificação de preço mínimo no PDV antes da venda"
status: pendente
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Integrar no frontend do PDV (`PDV.tsx`) a chamada ao endpoint
`POST /pdv/verificar-preco` (já existente no backend) para alertar o operador
quando um preço praticado está abaixo do preço mínimo calculado.

### Contexto

O backend já possui:
- Endpoint `POST /api/v1/pdv/verificar-preco` funcional
- Função `verificar_precos_minimos()` em `pdv_service.py`
- Testes passando em `test_pdv_preco_minimo.py` (6 cenários)

**O frontend não consulta esse endpoint.** O operador pode finalizar uma
venda abaixo do custo sem qualquer aviso.

### Ações

1. **Criar função de API** em `frontend/src/services/api.ts`:
   ```typescript
   export async function verificarPrecoMinimo(itens: ItemVerificacao[]): Promise<ResultadoVerificacao> {
     const { data } = await apiClient.post('/api/v1/pdv/verificar-preco', { itens })
     return data
   }
   ```

2. **Criar modal `ModalAlertaPrecoMinimo.tsx`** em `frontend/src/components/`:
   - Exibir tabela com:
     - Nome do produto
     - Preço praticado vs. preço mínimo
     - Prejuízo estimado por item
   - Dois botões:
     - "Corrigir Preços" → fecha o modal e volta ao PDV
     - "Vender Mesmo Assim" → prossegue com a venda
   - Ícone de ⚠️ e cor de alerta (amarelo/vermelho)

3. **Integrar no fluxo de finalização do `PDV.tsx`:**
   - **Antes** de chamar `POST /pdv/venda`, chamar `POST /pdv/verificar-preco`
   - Se `tem_alertas === true`:
     - Exibir `ModalAlertaPrecoMinimo`
     - Se o operador confirmar: prosseguir com a venda normal
     - Se o operador cancelar: voltar ao PDV para ajustar preços
   - Se `tem_alertas === false`: prosseguir direto

4. **Tratamento de erro:**
   - Se a chamada a `/pdv/verificar-preco` falhar (ex: timeout), **não
     bloquear** a venda — apenas logar o erro e prosseguir

### Critério de aceite

- Ao finalizar venda com preço abaixo do mínimo, modal de alerta aparece.
- Modal exibe dados corretos (preço praticado, mínimo, prejuízo).
- Operador pode escolher "Vender Mesmo Assim" ou "Corrigir".
- Venda com preço acima do mínimo finaliza sem modal adicional.
- Falha na verificação não impede a venda.
- Build sem erros.

### Branch sugerida

`frontend/pdv-verificar-preco-minimo`
