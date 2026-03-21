---
task_id: TASK-014
title: "Definir politica explicita de versionamento da API"
priority: baixa
scope: README.md, docs/, backend/app/main.py
branch: docs/politica-versionamento-api
commit_message: "docs(api): define politica de versionamento v1 legado e v2 ativo"
estimated_effort: 30 minutos
status: pendente
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

## Criterios de aceite
- [ ] Documento de politica publicado no repositorio
- [ ] README atualizado com status de versoes
- [ ] Endpoints novos marcados explicitamente como v2
- [ ] Plano de depreciacao de v1 descrito
