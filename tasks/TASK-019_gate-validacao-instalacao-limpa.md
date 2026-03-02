---
task_id: TASK-019
title: "Criar gate de validação em instalação limpa para release desktop"
priority: 🟡 média
scope: docs/, .github/workflows/
branch: ci/desktop-clean-install-gate
commit_message: "ci(qa): adiciona gate de validação para instalação limpa"
estimated_effort: 30 minutos
status: concluida
depends_on: ["TASK-018"]
recomendacao_ref: "docs/validacao_apresentacao_cliente.md seção 7"
agent_chat_executable: "nao"
agent_chat_reason: "Requer validacao manual em VM Windows limpa com checklist e evidencias."
---

# TASK-019: Gate obrigatório de instalação limpa

## Contexto
Antes de entrega ao cliente, o projeto define como obrigatório validar o
instalador em VM Windows limpa com checklist funcional.

## Objetivo
Padronizar o gate de qualidade da release desktop para evitar entrega sem
validação real de instalação.

## Critérios de aceite
- [x] Checklist de validação em VM limpa versionado no repositório
- [x] Processo de aprovação da release exige checklist 100% concluído
- [x] Evidências da validação (logs/screenshots) anexadas ao fluxo de release
- [x] Release não é marcada como pronta sem aprovação desse gate

## Registro de conclusão
- Validação manual em VM Windows limpa confirmada pelo solicitante em 2026-03-02.
- Gate considerado aprovado para continuidade da trilha desktop.
