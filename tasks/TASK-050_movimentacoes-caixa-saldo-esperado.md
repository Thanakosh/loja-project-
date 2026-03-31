---
task_id: TASK-050
title: "Movimentacoes de caixa e saldo esperado no fechamento"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-022"]
---

## Objetivo

Evoluir a aba de caixa para suportar operacao real de caixa diario, com
registro de sangria e suprimento, calculo de saldo esperado no fechamento,
separacao entre valor contado e valor esperado e rastreabilidade completa por
usuario e horario.

## Contexto

O projeto ja possui controle basico de abertura e fechamento de caixa em
`/api/v1/caixa`, com registro de:

- momento de abertura
- momento de fechamento
- valor de abertura
- valor de fechamento
- diferenca
- status
- usuario que abriu e usuario que fechou

Esse fluxo cobre o minimo, mas ainda nao atende a operacao diaria completa.
Hoje faltam eventos intermediarios que alteram o saldo fisico do caixa, como:

- sangria
- suprimento
- justificativa operacional de divergencias

Sem essas movimentacoes, a diferenca no fechamento fica pouco auditavel e o
caixa nao consegue informar com precisao quanto deveria existir fisicamente no
momento da conferencia.

## Escopo

### Backend

1. Criar estrutura para movimentacoes de caixa:
   - tabela/model `movimentacao_caixa`
   - tipos minimos: `sangria` e `suprimento`
   - campos: `id`, `caixa_id`, `tipo`, `valor`, `motivo`, `observacao`,
     `usuario_id`, `created_at`

2. Criar endpoints autenticados:
   - `POST /api/v1/caixa/{caixa_id}/movimentacoes`
   - `GET /api/v1/caixa/{caixa_id}/movimentacoes`

3. Garantir regras de negocio:
   - nao permitir movimentacao em caixa fechado
   - nao permitir valores menores ou iguais a zero
   - registrar usuario responsavel
   - calcular saldo esperado do caixa com base em:
     - valor de abertura
     - total de suprimentos
     - total de sangrias
     - vendas em dinheiro vinculadas ao caixa

4. Expor no resumo do caixa:
   - `saldo_esperado`
   - `total_sangrias`
   - `total_suprimentos`
   - `valor_em_dinheiro_vendas`

5. Exigir observacao no fechamento quando houver diferenca diferente de zero.

### Frontend

1. Atualizar a aba `CaixaDiario` para exibir:
   - saldo esperado atual
   - total de sangrias
   - total de suprimentos
   - valor contado no fechamento
   - diferenca entre contado e esperado

2. Adicionar acoes na UI:
   - botao de `Registrar Sangria`
   - botao de `Registrar Suprimento`
   - formulario com valor, motivo e observacao

3. Adicionar historico de movimentacoes do caixa aberto:
   - horario
   - tipo
   - valor
   - usuario
   - observacao

4. Melhorar o historico de caixas fechados para mostrar:
   - valor esperado no fechamento
   - valor contado
   - diferenca
   - usuario que abriu
   - usuario que fechou

### Testes

1. Backend:
   - abrir caixa e registrar suprimento
   - abrir caixa e registrar sangria
   - bloquear movimentacao em caixa fechado
   - recalcular saldo esperado corretamente
   - exigir observacao quando diferenca for diferente de zero

2. Frontend/E2E:
   - abrir caixa
   - registrar sangria
   - registrar suprimento
   - fechar caixa com saldo coerente
   - fechar caixa com diferenca e observacao obrigatoria

## Regras para implementacao

- Nao duplicar regra de negocio no frontend.
- O calculo de saldo esperado deve ficar integralmente no backend.
- Toda alteracao de modelo deve ter migracao Alembic dedicada.
- Toda movimentacao deve ficar vinculada ao usuario autenticado.
- A nomenclatura dos tipos de movimentacao deve ser simples e deterministica.

## Criterios de aceite

- Caixa aceita `sangria` e `suprimento` via API e UI.
- O sistema calcula `saldo_esperado` em tempo real no caixa aberto.
- O fechamento passa a distinguir claramente:
  - valor esperado
  - valor contado
  - diferenca
- Divergencia sem observacao e rejeitada pelo backend.
- Historico do caixa mostra movimentacoes e usuarios responsaveis.
- Testes automatizados cobrindo backend e fluxo integrado passam localmente.

## Fora de escopo nesta task

- reabertura de caixa fechado
- estorno manual de movimentacao
- permissao fina por acao de caixa
- exportacao PDF/CSV do historico de caixa
- dashboard grafico de caixa

## Branch sugerida

`feature/caixa-movimentacoes-saldo-esperado`
