---
task_id: TASK-015
title: "Planejar convergência para arquitetura async no banco"
priority: 🟢 arquitetura
scope: backend/app/core/database.py, backend/app/api/v1/, backend/tests/
branch: refactor/plano-migracao-async-db
commit_message: "refactor(db): define plano incremental de migração para AsyncSession"
estimated_effort: 60 minutos
status: pendente
depends_on: ["TASK-003"]
recomendacao_ref: "#13 — Convergência para arquitetura async no banco"
---

# TASK-015: Convergência para async no banco

## Contexto
A direção técnica prevê migração para `AsyncEngine/AsyncSession`,
mas ainda sem plano incremental versionado por módulo.

## Objetivo
Criar plano de migração faseado, iniciando por módulos de maior I/O
(OCR e estoque), com critérios de rollback e cobertura de testes.

## Critérios de aceite
- [ ] Documento técnico com fases da migração
- [ ] Lista de endpoints/módulos candidatos por ordem de risco
- [ ] Estratégia de testes antes/depois por módulo
- [ ] POC com pelo menos 1 endpoint assíncrono validado
