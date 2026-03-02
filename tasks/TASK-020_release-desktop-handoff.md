---
task_id: TASK-020
title: "Preparar handoff de release desktop para entrega ao cliente"
priority: 🔴 alta
scope: docs/, .github/workflows/, frontend/
branch: ci/desktop-release-handoff
commit_message: "ci(desktop): prepara handoff de release para entrega ao cliente"
estimated_effort: 60 minutos
status: pendente
depends_on: ["TASK-019"]
recomendacao_ref: "docs/validacao_apresentacao_cliente.md seção 6.2 e seção 8"
agent_chat_executable: "sim"
agent_chat_reason: "Escopo técnico/documental executável via repositório e CI."
---

# TASK-020: Handoff de release desktop

## Contexto
Com o gate de instalação limpa concluído, falta consolidar os artefatos de release
em um pacote operacional claro para entrega ao cliente e rastreabilidade interna.

## Objetivo
Padronizar o handoff da release desktop com artefatos, notas e checklist final de
entrega, reduzindo risco operacional na publicação.

## Critérios de aceite
- [ ] Job de release desktop publica `.exe` e checksum SHA256 como artifacts
- [ ] Nota de versão inclui mudanças, requisitos mínimos e instruções de instalação
- [ ] Checklist final de entrega ao cliente versionado em `docs/`
- [ ] Evidências de validação da VM limpa vinculadas na nota de release
