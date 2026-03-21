---
task_id: TASK-037
title: "Medir cobertura de testes e definir baseline"
status: pendente
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Medir a cobertura de testes atual do backend, gerar relatório e estabelecer
baseline para acompanhar evolução. Identificar módulos com menor cobertura
para priorizar futuras melhorias.

### Contexto

O projeto possui 36 arquivos de teste em `backend/tests/`. O KPI definido
em `RECOMENDACOES_TECNICAS.md` é ≥ 80% nos módulos críticos, mas não há
medição recente de cobertura.

### Ações

1. **Instalar pytest-cov** se não estiver no requirements:
   ```bash
   pip install pytest-cov
   ```
2. **Executar testes com cobertura:**
   ```bash
   cd backend
   pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=json:coverage.json -v
   ```
3. **Analisar o relatório e documentar:**
   - Cobertura geral (%)
   - Cobertura por módulo:
     - `app/api/v1/` (endpoints)
     - `app/core/` (segurança, config, exceptions)
     - `app/services/` (PDV, PDF, caixa)
     - `app/fiscal/` (motor de custo, normalizer, validator)
     - `app/models/` (modelos)
   - Top 5 arquivos com MENOR cobertura
   - Top 5 arquivos com MAIOR cobertura
4. **Criar relatório** em `docs/cobertura-testes-baseline.md` com:
   - Data da medição
   - Tabela de cobertura por módulo
   - Gráfico de distribuição (opcional)
   - Recomendações de onde investir em testes
5. **Adicionar `pytest-cov` ao `backend/requirements.txt`** como dependência
   de desenvolvimento (ou criar `backend/requirements-dev.txt`).
6. **Adicionar `htmlcov/` e `coverage.json` ao `.gitignore`.**

### Critério de aceite

- Relatório gerado com cobertura por módulo.
- `pytest-cov` configurado e funcionando.
- Baseline documentado para comparação futura.
- Artefatos de cobertura no `.gitignore`.

### Branch sugerida

`chore/cobertura-testes-baseline`
