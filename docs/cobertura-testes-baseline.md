# Baseline de Cobertura de Testes

Data da medicao: 2026-03-21

Comando utilizado:

```powershell
$env:DEBUG='false'; $env:ENVIRONMENT='test'; pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=json:coverage.json -v
```

## Resumo

- Cobertura geral do backend: `87.84%`
- Resultado da execucao: `375 passed, 1 failed`
- Falha encontrada na medicao inicial: leitura do `.gitignore` em codificacao nao UTF-8
- Ajuste aplicado nesta task: `.gitignore` normalizado em UTF-8 e artefatos de cobertura adicionados ao ignore

## Cobertura por modulo

| Modulo | Linhas cobertas | Linhas totais | Cobertura |
|--------|------------------|---------------|-----------|
| `app/api/v1/` | 1254 | 1490 | `84.16%` |
| `app/core/` | 583 | 749 | `77.84%` |
| `app/services/` | 381 | 408 | `93.38%` |
| `app/fiscal/` | 383 | 404 | `94.80%` |
| `app/models/` | 445 | 462 | `96.32%` |

## Top 5 arquivos com menor cobertura

| Arquivo | Cobertura |
|---------|-----------|
| `app/core/ocr_worker.py` | `0.00%` |
| `app/api/v1/estoque.py` | `43.18%` |
| `app/api/v1/ai.py` | `53.57%` |
| `app/ai/duplicate_detector.py` | `62.70%` |
| `app/api/v1/produto.py` | `70.65%` |

## Top 5 arquivos com maior cobertura

Considerando apenas arquivos com linhas executaveis (`num_statements > 0`):

| Arquivo | Cobertura |
|---------|-----------|
| `app/fiscal/cross_validator.py` | `100.00%` |
| `app/schemas/produto.py` | `100.00%` |
| `app/schemas/orcamento.py` | `100.00%` |
| `app/ai/audit_service.py` | `100.00%` |
| `app/api/v1/relatorios.py` | `100.00%` |

## Leitura tecnica

- O backend supera a meta minima global esperada para baseline.
- O principal ponto de risco esta em `app/core/`, puxado por `app/core/ocr_worker.py` sem cobertura.
- `app/api/v1/` tambem merece prioridade, especialmente endpoints legados e fluxos auxiliares de IA.
- `services`, `fiscal` e `models` estao em situacao boa para sustentar refatoracoes incrementais.

## Recomendacoes de investimento em testes

1. Cobrir `app/core/ocr_worker.py` com testes de fila, retry e expiracao.
2. Expandir testes de `app/api/v1/estoque.py` ou remover o legado se o fluxo oficial for apenas v2.
3. Aumentar cenarios de erro e fallback em `app/api/v1/ai.py` e `app/ai/duplicate_detector.py`.
4. Reforcar casos negativos e filtros de `app/api/v1/produto.py`.
5. Usar esta baseline antes de avancar em `TASK-042` para medir regressao da migracao async.
