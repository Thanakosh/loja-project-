---
task_id: TASK-016
title: "Separar dependências pesadas OCR/ML do core da API"
priority: 🟡 média
scope: backend/requirements.txt, backend/requirements-ocr.txt, README.md
branch: chore/split-deps-ocr-ml
commit_message: "chore(deps): separa dependências OCR/ML do núcleo da API"
estimated_effort: 30 minutos
status: concluída
depends_on: []
recomendacao_ref: "#14 — Desacoplamento de dependências pesadas"
---

# TASK-016: Split de dependências OCR/ML

## Contexto
Dependências pesadas de OCR/ML aumentam tempo de build e custo operacional
do ambiente base, mesmo quando funcionalidades não são utilizadas.

## Objetivo
Manter `backend/requirements.txt` mínimo para o core e mover dependências
pesadas para `backend/requirements-ocr.txt`.

## Critérios de aceite
- [x] Dependências OCR/ML separadas em arquivo dedicado
- [x] `requirements.txt` mantém apenas núcleo necessário da API
- [x] README documenta instalação por perfil (core vs OCR)
- [x] Build do ambiente base reduzido/mais rápido
