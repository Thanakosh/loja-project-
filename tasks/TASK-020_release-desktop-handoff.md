---
task_id: TASK-020
title: "Preparar handoff de release desktop para entrega ao cliente"
priority: alta
scope: docs/, .github/workflows/, frontend/
branch: ci/desktop-release-handoff
commit_message: "ci(desktop): prepara handoff de release para entrega ao cliente"
estimated_effort: 60 minutos
status: concluida
depends_on: ["TASK-019"]
recomendacao_ref: "docs/validacao_apresentacao_cliente.md secao 6.2 e secao 8"
agent_chat_executable: "sim"
agent_chat_reason: "Escopo tecnico/documental executavel via repositorio e CI."
---

# TASK-020: Handoff de release desktop

## Contexto
Com o gate de instalacao limpa concluido, falta consolidar os artefatos de release
em um pacote operacional claro para entrega ao cliente e rastreabilidade interna.

## Objetivo
Padronizar o handoff da release desktop com artefatos, notas e checklist final de
entrega, reduzindo risco operacional na publicacao.

## Criterios de aceite
- [x] Job de release desktop publica `.exe` e checksum SHA256 como artifacts
- [x] Nota de versao inclui mudancas, requisitos minimos e instrucoes de instalacao
- [x] Checklist final de entrega ao cliente versionado em `docs/`
- [x] Evidencias de validacao da VM limpa vinculadas na nota de release

## Entregaveis implementados
- Workflow: `.github/workflows/windows-desktop-build.yml`
- Nota de versao: `docs/releases/desktop-release-notes.md`
- Checklist de entrega: `docs/checklist-entrega-cliente.md`
- Evidencias: `docs/evidencias/TASK-019_validacao-vm-limpa.md`
