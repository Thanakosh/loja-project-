---
task_id: TASK-030
title: "Criar normalizador de payload fiscal interno"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-029"]
---

## Objetivo

Criar um payload canonico de nota fiscal para ser usado por auditoria,
precificacao e risco, evitando regras duplicadas em multiplos servicos.

### Acoes

1. Definir schema Pydantic v2 para payload normalizado em `backend/app/schemas/`.
2. Implementar normalizador unico (ex.: `backend/app/fiscal/normalizer.py`) a
   partir do output do parser de XML.
3. Versionar o formato interno (`versao_payload`) para permitir evolucao segura.
4. Adicionar testes unitarios para normalizacao e validacao de contrato.

### Criterio de aceite

- Existe um contrato interno unico e versionado para consumo dos modulos fiscais.
- Servicos novos usam o normalizador em vez de ler XML bruto diretamente.
