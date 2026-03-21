---
task_id: TASK-018
title: "Implementar pipeline GitHub Actions para build desktop Windows"
priority: alta
scope: .github/workflows/, frontend/package.json
branch: ci/windows-desktop-pipeline
commit_message: "ci(desktop): adiciona pipeline de build Windows com artefatos"
estimated_effort: 45 minutos
status: concluida
depends_on: ["TASK-017"]
recomendacao_ref: "docs/validacao_apresentacao_cliente.md secao 6.1 e 6.2"
---

# TASK-018: Pipeline Windows para gerar instalador

## Contexto
A recomendacao tecnica pede pipeline com runner `windows-latest`, build do
frontend desktop e publicacao de instalador `.exe`.

## Objetivo
Criar workflow de CI/CD para gerar artefatos minimos do release desktop.

## Criterios de aceite
- [x] Workflow acionado por tag de release (ex.: `v*-desktop.*`)
- [x] Job em `windows-latest` executa `npm ci`, `npm run build`, `npm run make`
- [x] Instalador `.exe` publicado como artifact
- [x] SHA256 do instalador gerado e publicado como artifact
- [x] Fail fast quando etapa de build ou empacotamento falhar
