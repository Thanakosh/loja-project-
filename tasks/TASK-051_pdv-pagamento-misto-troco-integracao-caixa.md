---
task_id: TASK-051
title: "PDV com pagamento misto, troco e integracao correta com caixa"
status: pendente
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-050"]
---

## Objetivo

Evoluir o PDV para suportar pagamento misto na mesma venda, calculo de troco
em dinheiro e integracao correta com o caixa, separando o que afeta saldo
fisico do que representa apenas faturamento por outros meios.

## Contexto

O PDV atual ja permite:

- registrar venda
- aplicar desconto por item e desconto geral
- vincular cliente
- operar com venda a prazo
- validar caixa aberto
- baixar estoque automaticamente
- cancelar venda com estorno

Mas o fluxo de recebimento ainda esta simplificado demais:

- a venda aceita apenas uma forma de pagamento principal
- nao ha pagamento misto
- nao ha calculo de troco
- o caixa ainda nao consegue refletir corretamente quanto entrou em dinheiro
  quando a venda usa mais de um meio de pagamento

Na operacao real, isso e uma lacuna importante. Exemplo comum:

- total da venda: `R$ 180,00`
- cliente paga `R$ 100,00` em dinheiro
- `R$ 80,00` em PIX

Ou:

- total da venda: `R$ 75,00`
- cliente entrega `R$ 100,00` em dinheiro
- sistema precisa calcular `R$ 25,00` de troco

Sem esse detalhamento, o PDV registra faturamento, mas nao fecha bem a
operacao de recebimento e caixa.

## Escopo

### Backend

1. Criar estrutura para pagamentos da venda:
   - tabela/model `venda_pagamento`
   - campos minimos:
     - `id`
     - `venda_id`
     - `forma_pagamento`
     - `valor`
     - `ordem`
     - `valor_recebido` (opcional, para dinheiro)
     - `troco` (opcional, para dinheiro)

2. Adaptar o schema do PDV:
   - manter compatibilidade com o payload atual durante a transicao
   - aceitar nova lista `pagamentos`
   - validar que a soma dos pagamentos cubra o total da venda

3. Regras de negocio:
   - permitir multiplos pagamentos na mesma venda
   - permitir troco apenas quando houver componente em `dinheiro`
   - impedir troco em formas nao fisicas como PIX, boleto e cartao
   - calcular `troco` no backend
   - rejeitar venda com soma insuficiente
   - manter suporte a venda `a prazo` sem misturar com pagamento imediato

4. Integracao com caixa:
   - apenas a parcela em `dinheiro` deve impactar saldo fisico do caixa
   - PIX, cartao e boleto entram no faturamento, mas nao no saldo fisico
   - expor no resumo da venda:
     - total recebido
     - total em dinheiro
     - total em pix
     - total em cartao
     - troco

5. Persistencia e consulta:
   - incluir pagamentos no retorno de `POST /api/v1/pdv/venda`
   - incluir pagamentos em `GET /api/v1/pdv/venda/{id}`
   - incluir pagamentos no historico de vendas quando necessario

### Frontend

1. Atualizar o PDV para suportar lista de pagamentos:
   - adicionar linhas de pagamento
   - selecionar forma de pagamento por linha
   - informar valor por linha
   - adicionar/remover linha de pagamento

2. Fluxo de dinheiro:
   - quando houver pagamento em dinheiro, permitir informar `valor recebido`
   - exibir `troco` calculado em tempo real
   - bloquear finalizacao se o valor for insuficiente

3. Fluxo de UX:
   - mostrar claramente:
     - total da venda
     - total informado nos pagamentos
     - restante
     - troco
   - impedir combinacoes invalidas
   - nao permitir misturar `a prazo` com outros meios na mesma venda, salvo se
     a regra de negocio futura decidir o contrario

4. Resultado da venda:
   - modal/confirmacao deve mostrar composicao dos pagamentos
   - comprovante deve incluir o detalhamento de pagamento e troco

### Relacao com Caixa

1. Preparar integracao com a `TASK-050`:
   - vendas em dinheiro devem alimentar corretamente o saldo esperado do caixa
   - troco deve reduzir o saldo liquido fisico
   - o caixa deve conseguir distinguir:
     - faturamento total da venda
     - entrada fisica em dinheiro
     - troco devolvido
     - entrada nao fisica (PIX/cartao)

## Regras para implementacao

- Nao duplicar calculos de pagamento no frontend.
- O backend deve ser a fonte da verdade para:
  - total pago
  - troco
  - validacao de suficiencia
  - impacto no caixa
- Toda alteracao de modelo deve ter migracao Alembic dedicada.
- Preservar compatibilidade com o fluxo atual de pagamento unico durante a
  transicao, se isso reduzir risco de regressao.

## Criterios de aceite

- PDV aceita pagamento misto na mesma venda.
- PDV calcula troco corretamente para vendas com dinheiro.
- Backend rejeita combinacoes invalidas de pagamento.
- Caixa passa a refletir apenas o impacto fisico em dinheiro.
- Detalhamento de pagamentos aparece no retorno da venda e no comprovante.
- Testes automatizados cobrem backend e fluxo integrado do frontend.

## Testes esperados

1. Backend:
   - venda com pagamento unico em dinheiro
   - venda com pagamento misto dinheiro + PIX
   - venda com troco em dinheiro
   - venda com soma insuficiente rejeitada
   - venda com troco em forma nao permitida rejeitada
   - venda a prazo continua funcionando conforme regra definida

2. Frontend/E2E:
   - finalizar venda com dinheiro e troco
   - finalizar venda com dinheiro + PIX
   - validar bloqueio para pagamento insuficiente
   - validar comprovante com composicao de pagamentos

## Fora de escopo nesta task

- integracao TEF com maquininhas
- PIX com QR code dinamico
- conciliacao financeira bancaria
- NFC-e/SAT/ECF
- split de pagamento entre varios clientes

## Branch sugerida

`feature/pdv-pagamento-misto-troco`
