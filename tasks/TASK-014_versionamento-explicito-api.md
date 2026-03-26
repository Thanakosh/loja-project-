---
task_id: TASK-014
title: "Definir politica explicita de versionamento da API"
priority: baixa
scope: README.md, docs/, backend/app/main.py
branch: docs/politica-versionamento-api
commit_message: "docs(api): define politica de versionamento v1 legado e v2 ativo"
estimated_effort: 30 minutos
status: concluida
depends_on: []
recomendacao_ref: "#12 Estrategia explicita de versionamento de API"
---

# TASK-014: Politica de versionamento de API

## Contexto
Ha coexistencia de endpoints legados e ativos, mas sem politica formal
versionada para depreciacao e adocao de novos endpoints.

## Objetivo
Documentar e aplicar politica oficial:
- v1 = legado (manutencao corretiva)
- v2 = versao ativa para novas features
- cronograma de depreciacao para rotas legadas

## Atualizacao 2026-03-22

Task concluida.

Evidencias no repositorio:
- politica publicada em `docs/POLITICA_VERSIONAMENTO_API.md`
- README atualizado com status de versoes e orientacao de uso
- headers de depreciacao aplicados em `backend/app/main.py` para
  `/api/v1/estoque`

## Criterios de aceite
- [x] Documento de politica publicado no repositorio
- [x] README atualizado com status de versoes
- [x] Endpoints novos marcados explicitamente como v2
- [x] Plano de depreciacao de v1 descrito
