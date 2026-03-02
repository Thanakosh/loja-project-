---
task_id: TASK-020
title: "Preparar handoff de release desktop para entrega ao cliente"
priority: 🔴 alta
scope: docs/, .github/workflows/, frontend/
branch: ci/desktop-release-handoff
commit_message: "ci(desktop): prepara handoff de release para entrega ao cliente"
estimated_effort: 60 minutos
status: concluida
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
- [x] Job de release desktop publica `.exe` e checksum SHA256 como artifacts
- [x] Nota de versão inclui mudanças, requisitos mínimos e instruções de instalação
- [x] Checklist final de entrega ao cliente versionado em `docs/`
- [x] Evidências de validação da VM limpa vinculadas na nota de release

## Entregáveis implementados
- Workflow: `.github/workflows/windows-desktop-build.yml`
- Nota de versão: `docs/releases/desktop-release-notes.md`
- Checklist de entrega: `docs/checklist-entrega-cliente.md`
- Evidências: `docs/evidencias/TASK-019_validacao-vm-limpa.md`
