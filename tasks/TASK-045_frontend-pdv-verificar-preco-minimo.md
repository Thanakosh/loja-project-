---
task_id: TASK-045
title: "Frontend: verificacao de preco minimo no PDV antes da venda"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Integrar no frontend do PDV (`PDV.tsx`) a chamada ao endpoint
`POST /pdv/verificar-preco` (ja existente no backend) para alertar o operador
quando um preco praticado esta abaixo do preco minimo calculado.

### Contexto

O backend ja possui:
- Endpoint `POST /api/v1/pdv/verificar-preco` funcional
- Funcao `verificar_precos_minimos()` em `pdv_service.py`
- Testes passando em `test_pdv_preco_minimo.py` (6 cenarios)

**O frontend nao consulta esse endpoint.** O operador pode finalizar uma
venda abaixo do custo sem qualquer aviso.

### Acoes

1. **Criar funcao de API** em `frontend/src/services/api.ts`:
   ```typescript
   export async function verificarPrecoMinimo(itens: ItemVerificacao[]): Promise<ResultadoVerificacao> {
     const { data } = await apiClient.post('/api/v1/pdv/verificar-preco', { itens })
     return data
   }
   ```

2. **Criar modal `ModalAlertaPrecoMinimo.tsx`** em `frontend/src/components/`:
   - Exibir tabela com:
     - Nome do produto
     - Preco praticado vs. preco minimo
     - Prejuizo estimado por item
   - Dois botoes:
     - "Corrigir Precos"  fecha o modal e volta ao PDV
     - "Vender Mesmo Assim"  prossegue com a venda
   - Icone de  e cor de alerta (amarelo/vermelho)

3. **Integrar no fluxo de finalizacao do `PDV.tsx`:**
   - **Antes** de chamar `POST /pdv/venda`, chamar `POST /pdv/verificar-preco`
   - Se `tem_alertas === true`:
     - Exibir `ModalAlertaPrecoMinimo`
     - Se o operador confirmar: prosseguir com a venda normal
     - Se o operador cancelar: voltar ao PDV para ajustar precos
   - Se `tem_alertas === false`: prosseguir direto

4. **Tratamento de erro:**
   - Se a chamada a `/pdv/verificar-preco` falhar (ex: timeout), **nao
     bloquear** a venda - apenas logar o erro e prosseguir

### Criterio de aceite

- Ao finalizar venda com preco abaixo do minimo, modal de alerta aparece.
- Modal exibe dados corretos (preco praticado, minimo, prejuizo).
- Operador pode escolher "Vender Mesmo Assim" ou "Corrigir".
- Venda com preco acima do minimo finaliza sem modal adicional.
- Falha na verificacao nao impede a venda.
- Build sem erros.

### Branch sugerida

`frontend/pdv-verificar-preco-minimo`
