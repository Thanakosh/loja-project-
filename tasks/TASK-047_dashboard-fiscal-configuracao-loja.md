---
task_id: TASK-047
title: "Dashboard: card de saúde fiscal + configuração de regime tributário"
status: concluido
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-044"]
---

## Objetivo

Adicionar ao Dashboard um card de "Saúde Fiscal" consumindo o endpoint
existente, e criar modelo de configurações da loja (regime tributário, UF,
margens) para contextualizar as verificações fiscais.

### Contexto

O backend já possui `GET /fiscal-ai/risk-dashboard` funcional, mas o frontend
`Dashboard.tsx` (8KB) **não o consome**. Além disso, as verificações fiscais
usam valores hardcoded (ex: `margem_minima_percentual=0.05`,
`regime_tributario=None`) que deveriam ser parametrizáveis por loja.

Este task combina a **Fase 4** (painel fiscal no dashboard) + **Fase 5**
(configuração de regime tributário) do plano original.

### Ações

#### Parte A — Card de Saúde Fiscal no Dashboard

1. **Adicionar ao `Dashboard.tsx`:**
   - Novo card "Saúde Fiscal" com:
     - Score médio de risco das últimas N notas importadas
     - Quantidade de notas com risco alto
     - Top 3 fornecedores com mais alertas
     - Indicador visual (barra ou gauge) do score
   - Consumir `GET /api/v1/fiscal-ai/risk-dashboard` (endpoint já existe)
   - Tratar caso de zero notas importadas (exibir estado vazio)

#### Parte B — Modelo de Configurações da Loja

2. **Backend — Criar modelo `ConfiguracaoLoja`:**
   - Arquivo: `backend/app/models/configuracao_loja.py`
   - Campos:
     - `id` (PK)
     - `regime_tributario` (enum: 'simples_nacional', 'regime_normal')
     - `uf` (sigla com 2 caracteres: SP, RJ, MG, etc.)
     - `margem_minima_percentual` (float, default 0.05)
     - `aliquota_impostos_default` (float, opcional)
     - `updated_at` (timestamp)
   - Singleton: só deve existir 1 registro (ou usar a última)

3. **Backend — Criar endpoints CRUD:**
   - Arquivo: `backend/app/api/v1/configuracoes.py`
   - `GET /api/v1/configuracoes/loja` — retorna configuração atual
   - `PUT /api/v1/configuracoes/loja` — atualiza configuração
   - Autenticação obrigatória

4. **Backend — Integrar nos fluxos fiscais:**
   - `ocr.py`: ler `regime_tributario` e `uf` das configurações para passar
     ao `auditar_nota_fiscal()` em vez de `None`
   - `pdv_service.py`: ler `margem_minima_percentual` das configurações em
     vez do hardcoded `0.05`

5. **Criar migração Alembic:**
   ```bash
   alembic revision --autogenerate -m "20260321_configuracao_loja"
   ```

6. **Frontend — Tela de configurações (opcional nesta iteração):**
   - Página ou modal simples em Configurações com campos de regime, UF e margem
   - Pode ser adicionada em task futura se necessário

7. **Testes:**
   - Teste do endpoint GET/PUT de configurações
   - Teste de que a auditoria fiscal usa regime da configuração
   - Teste de que o PDV usa margem da configuração

### Critério de aceite

- Dashboard exibe card de saúde fiscal com dados reais.
- Modelo `ConfiguracaoLoja` criado com migração.
- Endpoints GET/PUT funcionais e autenticados.
- Auditoria fiscal e PDV lêem parâmetros da configuração.
- Testes passando.

### Branch sugerida

`feat/dashboard-fiscal-configuracao-loja`
