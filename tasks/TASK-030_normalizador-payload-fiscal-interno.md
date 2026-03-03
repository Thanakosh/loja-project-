---
task_id: TASK-030
title: "Criar normalizador de payload fiscal interno"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-029"]
---

## Objetivo

Criar um payload canônico de nota fiscal para ser usado por auditoria,
precificação e risco, evitando regras duplicadas em múltiplos serviços.

### Ações

1. Definir schema Pydantic v2 para payload normalizado em `backend/app/schemas/`.
2. Implementar normalizador único (ex.: `backend/app/fiscal/normalizer.py`) a
   partir do output do parser de XML.
3. Versionar o formato interno (`versao_payload`) para permitir evolução segura.
4. Adicionar testes unitários para normalização e validação de contrato.

### Critério de aceite

- Existe um contrato interno único e versionado para consumo dos módulos fiscais.
- Serviços novos usam o normalizador em vez de ler XML bruto diretamente.
