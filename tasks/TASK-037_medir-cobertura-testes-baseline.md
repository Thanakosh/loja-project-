---
task_id: TASK-037
title: "Medir cobertura de testes e definir baseline"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Medir a cobertura de testes atual do backend, gerar relatorio e estabelecer
baseline para acompanhar evolucao. Identificar modulos com menor cobertura
para priorizar futuras melhorias.

### Contexto

O projeto possui 36 arquivos de teste em `backend/tests/`. O KPI definido
em `RECOMENDACOES_TECNICAS.md` e  80% nos modulos criticos, mas nao ha
medicao recente de cobertura.

### Acoes

1. **Instalar pytest-cov** se nao estiver no requirements:
   ```bash
   pip install pytest-cov
   ```
2. **Executar testes com cobertura:**
   ```bash
   cd backend
   pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=json:coverage.json -v
   ```
3. **Analisar o relatorio e documentar:**
   - Cobertura geral (%)
   - Cobertura por modulo:
     - `app/api/v1/` (endpoints)
     - `app/core/` (seguranca, config, exceptions)
     - `app/services/` (PDV, PDF, caixa)
     - `app/fiscal/` (motor de custo, normalizer, validator)
     - `app/models/` (modelos)
   - Top 5 arquivos com MENOR cobertura
   - Top 5 arquivos com MAIOR cobertura
4. **Criar relatorio** em `docs/cobertura-testes-baseline.md` com:
   - Data da medicao
   - Tabela de cobertura por modulo
   - Grafico de distribuicao (opcional)
   - Recomendacoes de onde investir em testes
5. **Adicionar `pytest-cov` ao `backend/requirements.txt`** como dependencia
   de desenvolvimento (ou criar `backend/requirements-dev.txt`).
6. **Adicionar `htmlcov/` e `coverage.json` ao `.gitignore`.**

### Criterio de aceite

- Relatorio gerado com cobertura por modulo.
- `pytest-cov` configurado e funcionando.
- Baseline documentado para comparacao futura.
- Artefatos de cobertura no `.gitignore`.

### Branch sugerida

`chore/cobertura-testes-baseline`

## Atualizacao de status

- Baseline medida em 2026-03-21 com cobertura total de `87.84%`.
- Relatorio gerado em `docs/cobertura-testes-baseline.md`.
- `pytest-cov` adicionado em `backend/requirements.txt`.
- `.gitignore` atualizado para ignorar `coverage.json`, `htmlcov/` e `.coverage`.
