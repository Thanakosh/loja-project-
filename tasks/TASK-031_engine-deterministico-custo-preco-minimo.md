---
task_id: TASK-031
title: "Implementar engine deterministico de custo e preco minimo"
status: concluido
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-030"]
---

## Objetivo

Entregar o nucleo deterministico de calculo de custo e preco minimo como base
obrigatoria antes de qualquer camada de IA generativa.

### Acoes

1. Criar `backend/app/fiscal/cost_calculator.py` com calculo de:
   - custo total
   - custo unitario
   - margem minima
   - preco minimo absoluto
2. Implementar regras explicitas para bloquear sugestoes abaixo do minimo.
3. Expor endpoint inicial `POST /api/v1/fiscal-ai/suggest-price/{product_id}`
   com autenticacao obrigatoria.
4. Registrar metadados de auditoria da regra aplicada (`versao_motor`).
5. Adicionar testes de API e de calculo com cenarios de borda.

### Criterio de aceite

- Endpoint retorna faixa de preco com minimo garantido por regra deterministica.
- Nenhum resultado permitido abaixo do preco minimo absoluto.
