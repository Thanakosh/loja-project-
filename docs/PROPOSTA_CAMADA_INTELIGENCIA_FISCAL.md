# Proposta Avaliada — Camada de Inteligência Fiscal com IA

## Status da avaliação

A proposta é **viável** e está alinhada com os objetivos do Loja Project (redução de erro tributário, melhoria de cadastro e proteção de margem), mas precisa de ajustes para aderir melhor à arquitetura atual do repositório.

---

## O que já existe no projeto (base para evoluir)

- Importação de NFe por XML já implementada no backend, com extração de fornecedor, itens, NCM e valor total.  
- Endpoints LLM existentes estão desativados e indicam retorno futuro com arquitetura mais robusta (fila assíncrona + persistência).
- Há módulo de estoque v2 e trilha de movimentações no backend, o que facilita calcular custo e risco de margem com dados transacionais.

---

## Ajustes recomendados na arquitetura proposta

A proposta original usa caminhos genéricos como `/app/fiscal` e `/app/ai`. No repositório atual, o padrão é `backend/app/...`.

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

> Observação: `backend/app/core/nfe_parser.py` já existe e pode ser evoluído incrementalmente em vez de duplicado.

---

## Verificação da proposta por bloco funcional

## 1) Importação XML de fornecedor

**Aderência:** alta.  
**Comentários:** já existe parser funcional. Faltam campos para auditoria avançada (CFOP, CST, ICMS por item, rateio de frete por item).

**Decisão recomendada:**
- Evoluir parser atual para expor campos fiscais por item.
- Criar normalizador para payload interno único usado por auditoria e pricing.

---

## 2) Auditoria fiscal com IA

**Aderência:** alta.  
**Comentários:** excelente escopo inicial (inconsistências + duplicidade), mas precisa separar regras determinísticas da camada IA.

**Decisão recomendada:**
- `fiscal/engine.py`: regras determinísticas (ex.: CST incompatível com regime, faixa esperada de alíquota, outlier de preço).
- `ai/audit_service.py`: ranking de risco e explicações em linguagem natural.
- Matching de produto com similaridade textual inicialmente (TF-IDF/cosseno), e embeddings em fase 2 para reduzir custo inicial.

---

## 3) Sugestão de preço mínimo inteligente

**Aderência:** muito alta.  
**Comentários:** fórmula determinística está correta como baseline e deve ser obrigatória antes de qualquer heurística de IA.

**Decisão recomendada:**
- `fiscal/cost_calculator.py` calcula preço mínimo absoluto e bloqueia sugestão abaixo do limite.
- `ai/pricing_service.py` sugere faixa (`minimo`, `seguro`, `competitivo`) com explicação e nível de risco.
- Salvar versão da regra/modelo usada na recomendação para auditoria futura.

---

## 4) Análise de risco tributário

**Aderência:** alta.  
**Comentários:** painel é coerente com frontend React/Electron e com o objetivo de operação assistida.

**Decisão recomendada:**
- Iniciar por API de risco com classificação `baixo/médio/alto`.
- Frontend consome apenas resultado pronto; regra fiscal continua centralizada no backend.

---

## 5) Aprendizado contínuo

**Aderência:** alta.  
**Comentários:** tabela `fiscal_feedback` é essencial para melhoria contínua e governança.

**Decisão recomendada:**
- Adicionar colunas de rastreabilidade: `origem_sugestao`, `versao_motor`, `created_at`, `user_id`.
- Treino/ajuste assíncrono por lote (não em tempo real na requisição HTTP).

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

- Manter autenticação obrigatória (`get_current_active_user`) em todos os endpoints.
- Evitar `dict` genérico no contrato: usar schemas Pydantic v2.

---

## Riscos e mitigação

- **Risco:** decisões automáticas opacas.  
  **Mitigação:** retornar sempre `explicacao`, `fatores` e `confianca`.
- **Risco:** custo/latência de embeddings cedo demais.  
  **Mitigação:** fasear em TF-IDF primeiro e ativar embeddings sob feature flag.
- **Risco:** divergência entre regra e IA.  
  **Mitigação:** IA nunca pode liberar preço abaixo do mínimo determinístico.

---

## Roadmap validado (incremental)

### Fase 1 (baixo risco)
- Evolução do parser XML com campos fiscais faltantes.
- Engine determinístico de custo e margem mínima.
- Endpoint de sugestão de preço mínimo sem IA generativa.

### Fase 2
- Auditoria fiscal híbrida (regras + score IA).
- Deteção de possíveis duplicados por similaridade textual.
- Coleta de feedback do usuário.

### Fase 3
- Precificação estratégica com histórico de giro.
- Painel consolidado de risco fiscal.
- Melhoria contínua orientada por `fiscal_feedback`.

---

## Conclusão

A proposta é consistente e agrega valor direto para operação e conformidade fiscal. A recomendação é seguir com implementação em fases curtas, priorizando **motor determinístico + observabilidade + feedback** antes de aumentar complexidade de IA.
