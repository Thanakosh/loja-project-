---
task_id: TASK-031
title: "Implementar engine determinístico de custo e preço mínimo"
status: concluido
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-030"]
---

## Objetivo

Entregar o núcleo determinístico de cálculo de custo e preço mínimo como base
obrigatória antes de qualquer camada de IA generativa.

### Ações

1. Criar `backend/app/fiscal/cost_calculator.py` com cálculo de:
   - custo total
   - custo unitário
   - margem mínima
   - preço mínimo absoluto
2. Implementar regras explícitas para bloquear sugestões abaixo do mínimo.
3. Expor endpoint inicial `POST /api/v1/fiscal-ai/suggest-price/{product_id}`
   com autenticação obrigatória.
4. Registrar metadados de auditoria da regra aplicada (`versao_motor`).
5. Adicionar testes de API e de cálculo com cenários de borda.

### Critério de aceite

- Endpoint retorna faixa de preço com mínimo garantido por regra determinística.
- Nenhum resultado permitido abaixo do preço mínimo absoluto.
