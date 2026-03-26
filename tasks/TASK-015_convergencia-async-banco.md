---
task_id: TASK-015
title: "Planejar convergencia para arquitetura async no banco"
priority: arquitetura
scope: backend/app/core/database.py, backend/app/api/v1/, backend/tests/
branch: refactor/plano-migracao-async-db
commit_message: "refactor(db): define plano incremental de migracao para AsyncSession"
estimated_effort: 60 minutos
status: concluida
depends_on: ["TASK-003"]
recomendacao_ref: "#13 Convergencia para arquitetura async no banco"
---

# TASK-015: Convergencia para async no banco

## Contexto
A direcao tecnica preve migracao para `AsyncEngine/AsyncSession`,
mas ainda sem plano incremental versionado por modulo.

## Objetivo
Criar plano de migracao faseado, iniciando por modulos de maior I/O
(OCR e estoque), com criterios de rollback e cobertura de testes.

## Atualizacao 2026-03-22

Task concluida.

Evidencias no repositorio:
- plano publicado em `docs/PLANO_MIGRACAO_ASYNC_DB.md`
- infraestrutura async em `backend/app/core/database.py`
- POC async publicada em `GET /api/v2/health-async`
  (`backend/app/api/v1/health_async.py`)

## Criterios de aceite
- [x] Documento tecnico com fases da migracao
- [x] Lista de endpoints/modulos candidatos por ordem de risco
- [x] Estrategia de testes antes/depois por modulo
- [x] POC com pelo menos 1 endpoint assincrono validado
