---
task_id: TASK-019
title: "Criar gate de validacao em instalacao limpa para release desktop"
priority: media
scope: docs/, .github/workflows/
branch: ci/desktop-clean-install-gate
commit_message: "ci(qa): adiciona gate de validacao para instalacao limpa"
estimated_effort: 30 minutos
status: concluida
depends_on: ["TASK-018"]
recomendacao_ref: "docs/validacao_apresentacao_cliente.md secao 7"
agent_chat_executable: "nao"
agent_chat_reason: "Requer validacao manual em VM Windows limpa com checklist e evidencias."
---

# TASK-019: Gate obrigatorio de instalacao limpa

## Contexto
Antes de entrega ao cliente, o projeto define como obrigatorio validar o
instalador em VM Windows limpa com checklist funcional.

## Objetivo
Padronizar o gate de qualidade da release desktop para evitar entrega sem
validacao real de instalacao.

## Criterios de aceite
- [x] Checklist de validacao em VM limpa versionado no repositorio
- [x] Processo de aprovacao da release exige checklist 100% concluido
- [x] Evidencias da validacao (logs/screenshots) anexadas ao fluxo de release
- [x] Release nao e marcada como pronta sem aprovacao desse gate

## Registro de conclusao
- Validacao manual em VM Windows limpa confirmada pelo solicitante em 2026-03-02.
- Gate considerado aprovado para continuidade da trilha desktop.
