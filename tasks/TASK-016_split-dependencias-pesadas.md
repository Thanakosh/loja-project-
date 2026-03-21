---
task_id: TASK-016
title: "Separar dependencias pesadas OCR/ML do core da API"
priority: media
scope: backend/requirements.txt, backend/requirements-ocr.txt, README.md
branch: chore/split-deps-ocr-ml
commit_message: "chore(deps): separa dependencias OCR/ML do nucleo da API"
estimated_effort: 30 minutos
status: concluida
depends_on: []
recomendacao_ref: "#14 Desacoplamento de dependencias pesadas"
---

# TASK-016: Split de dependencias OCR/ML

## Contexto
Dependencias pesadas de OCR/ML aumentam tempo de build e custo operacional
do ambiente base, mesmo quando funcionalidades nao sao utilizadas.

## Objetivo
Manter `backend/requirements.txt` minimo para o core e mover dependencias
pesadas para `backend/requirements-ocr.txt`.

## Criterios de aceite
- [x] Dependencias OCR/ML separadas em arquivo dedicado
- [x] `requirements.txt` mantem apenas nucleo necessario da API
- [x] README documenta instalacao por perfil (core vs OCR)
- [x] Build do ambiente base reduzido/mais rapido
