---
task_id: TASK-017
title: "Configurar Electron Forge para empacotamento desktop"
priority: 🟡 média
scope: frontend/package.json, frontend/electron/, frontend/vite.config.ts
branch: feat/electron-forge-setup
commit_message: "feat(frontend): configura base Electron Forge para build desktop"
estimated_effort: 60 minutos
status: pendente
depends_on: []
recomendacao_ref: "docs/validacao_apresentacao_cliente.md seção 6.1"
---

# TASK-017: Setup base do desktop com Electron Forge

## Contexto
O pipeline de build Windows depende de scripts de empacotamento desktop ativos.
Hoje o frontend está em React + Vite, mas sem fluxo de Electron habilitado.

## Objetivo
Criar base mínima de Electron Forge para permitir `npm run make` e gerar
artefato instalável em Windows.

## Critérios de aceite
- [ ] Electron Forge instalado e configurado no frontend
- [ ] Scripts de desktop adicionados no `package.json` (`start`, `package`, `make`)
- [ ] Build web (`npm run build`) continua funcionando
- [ ] `npm run make` executa localmente sem quebrar o projeto
