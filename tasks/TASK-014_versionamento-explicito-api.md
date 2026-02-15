---
task_id: TASK-014
title: "Definir política explícita de versionamento da API"
priority: 🟢 baixa
scope: README.md, docs/, backend/app/main.py
branch: docs/politica-versionamento-api
commit_message: "docs(api): define política de versionamento v1 legado e v2 ativo"
estimated_effort: 30 minutos
status: pendente
depends_on: []
recomendacao_ref: "#12 — Estratégia explícita de versionamento de API"
---

# TASK-014: Política de versionamento de API

## Contexto
Há coexistência de endpoints legados e ativos, mas sem política formal
versionada para depreciação e adoção de novos endpoints.

## Objetivo
Documentar e aplicar política oficial:
- v1 = legado (manutenção corretiva)
- v2 = versão ativa para novas features
- cronograma de depreciação para rotas legadas

## Critérios de aceite
- [ ] Documento de política publicado no repositório
- [ ] README atualizado com status de versões
- [ ] Endpoints novos marcados explicitamente como v2
- [ ] Plano de depreciação de v1 descrito
