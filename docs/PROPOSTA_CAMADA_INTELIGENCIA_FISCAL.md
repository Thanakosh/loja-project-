# Proposta Avaliada - Camada de Inteligencia Fiscal com IA

## Status da avaliacao

A proposta e **viavel** e esta alinhada com os objetivos do Loja Project (reducao de erro tributario, melhoria de cadastro e protecao de margem), mas precisa de ajustes para aderir melhor a arquitetura atual do repositorio.

---

## O que ja existe no projeto (base para evoluir)

- Importacao de NFe por XML ja implementada no backend, com extracao de fornecedor, itens, NCM e valor total.
- Endpoints LLM existentes estao desativados e indicam retorno futuro com arquitetura mais robusta (fila assincrona + persistencia).
- Ha modulo de estoque v2 e trilha de movimentacoes no backend, o que facilita calcular custo e risco de margem com dados transacionais.

---

## Ajustes recomendados na arquitetura proposta

A proposta original usa caminhos genericos como `/app/fiscal` e `/app/ai`. No repositorio atual, o padrao e `backend/app/...`.

### Estrutura sugerida (aderente ao projeto)

```text
backend/app/
  fiscal/
    engine.py
    cost_calculator.py
    risk_analyzer.py
  ai/
    audit_service.py
    pricing_service.py
    product_matching_service.py
  ingest/
    nfe_parser_v2.py
  models/
    fiscal_feedback.py
  schemas/
    fiscal_ai.py
  api/v1/
    fiscal_ai.py
backend/tests/
  test_fiscal_engine.py
  test_fiscal_ai_audit.py
  test_fiscal_ai_pricing.py
```

> Observacao: `backend/app/core/nfe_parser.py` ja existe e pode ser evoluido incrementalmente em vez de duplicado.

---

## Verificacao da proposta por bloco funcional

## 1) Importacao XML de fornecedor

**Aderencia:** alta.
**Comentarios:** ja existe parser funcional. Faltam campos para auditoria avancada (CFOP, CST, ICMS por item, rateio de frete por item).

**Decisao recomendada:**
- Evoluir parser atual para expor campos fiscais por item.
- Criar normalizador para payload interno unico usado por auditoria e pricing.

---

## 2) Auditoria fiscal com IA

**Aderencia:** alta.
**Comentarios:** excelente escopo inicial (inconsistencias + duplicidade), mas precisa separar regras deterministicas da camada IA.

**Decisao recomendada:**
- `fiscal/engine.py`: regras deterministicas (ex.: CST incompativel com regime, faixa esperada de aliquota, outlier de preco).
- `ai/audit_service.py`: ranking de risco e explicacoes em linguagem natural.
- Matching de produto com similaridade textual inicialmente (TF-IDF/cosseno), e embeddings em fase 2 para reduzir custo inicial.

---

## 3) Sugestao de preco minimo inteligente

**Aderencia:** muito alta.
**Comentarios:** formula deterministica esta correta como baseline e deve ser obrigatoria antes de qualquer heuristica de IA.

**Decisao recomendada:**
- `fiscal/cost_calculator.py` calcula preco minimo absoluto e bloqueia sugestao abaixo do limite.
- `ai/pricing_service.py` sugere faixa (`minimo`, `seguro`, `competitivo`) com explicacao e nivel de risco.
- Salvar versao da regra/modelo usada na recomendacao para auditoria futura.

---

## 4) Analise de risco tributario

**Aderencia:** alta.
**Comentarios:** painel e coerente com frontend React/Electron e com o objetivo de operacao assistida.

**Decisao recomendada:**
- Iniciar por API de risco com classificacao `baixo/medio/alto`.
- Frontend consome apenas resultado pronto; regra fiscal continua centralizada no backend.

---

## 5) Aprendizado continuo

**Aderencia:** alta.
**Comentarios:** tabela `fiscal_feedback` e essencial para melhoria continua e governanca.

**Decisao recomendada:**
- Adicionar colunas de rastreabilidade: `origem_sugestao`, `versao_motor`, `created_at`, `user_id`.
- Treino/ajuste assincrono por lote (nao em tempo real na requisicao HTTP).

---

## Endpoints recomendados (revisados)

```python
@router.post("/fiscal-ai/validate-note")
def validate_note(payload: FiscalNotePayload):
    ...

@router.post("/fiscal-ai/suggest-price/{product_id}")
def suggest_price(product_id: int):
    ...

@router.get("/fiscal-ai/risk-dashboard")
def risk_dashboard(...):
    ...

@router.post("/fiscal-ai/feedback")
def register_feedback(payload: FiscalFeedbackCreate):
    ...
```

- Manter autenticacao obrigatoria (`get_current_active_user`) em todos os endpoints.
- Evitar `dict` generico no contrato: usar schemas Pydantic v2.

---

## Riscos e mitigacao

- **Risco:** decisoes automaticas opacas.
  **Mitigacao:** retornar sempre `explicacao`, `fatores` e `confianca`.
- **Risco:** custo/latencia de embeddings cedo demais.
  **Mitigacao:** fasear em TF-IDF primeiro e ativar embeddings sob feature flag.
- **Risco:** divergencia entre regra e IA.
  **Mitigacao:** IA nunca pode liberar preco abaixo do minimo deterministico.

---

## Roadmap validado (incremental)

### Fase 1 (baixo risco)
- Evolucao do parser XML com campos fiscais faltantes.
- Engine deterministico de custo e margem minima.
- Endpoint de sugestao de preco minimo sem IA generativa.

### Fase 2
- Auditoria fiscal hibrida (regras + score IA).
- Detecao de possiveis duplicados por similaridade textual.
- Coleta de feedback do usuario.

### Fase 3
- Precificacao estrategica com historico de giro.
- Painel consolidado de risco fiscal.
- Melhoria continua orientada por `fiscal_feedback`.

---

## Conclusao

A proposta e consistente e agrega valor direto para operacao e conformidade fiscal. A recomendacao e seguir com implementacao em fases curtas, priorizando **motor deterministico + observabilidade + feedback** antes de aumentar complexidade de IA.
