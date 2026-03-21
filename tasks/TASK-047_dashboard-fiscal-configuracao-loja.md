---
task_id: TASK-047
title: "Dashboard: card de saude fiscal + configuracao de regime tributario"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-044"]
---

## Objetivo

Adicionar ao Dashboard um card de "Saude Fiscal" consumindo o endpoint
existente, e criar modelo de configuracoes da loja (regime tributario, UF,
margens) para contextualizar as verificacoes fiscais.

### Contexto

O backend ja possui `GET /fiscal-ai/risk-dashboard` funcional, mas o frontend
`Dashboard.tsx` (8KB) **nao o consome**. Alem disso, as verificacoes fiscais
usam valores hardcoded (ex: `margem_minima_percentual=0.05`,
`regime_tributario=None`) que deveriam ser parametrizaveis por loja.

Este task combina a **Fase 4** (painel fiscal no dashboard) + **Fase 5**
(configuracao de regime tributario) do plano original.

### Acoes

#### Parte A - Card de Saude Fiscal no Dashboard

1. **Adicionar ao `Dashboard.tsx`:**
   - Novo card "Saude Fiscal" com:
     - Score medio de risco das ultimas N notas importadas
     - Quantidade de notas com risco alto
     - Top 3 fornecedores com mais alertas
     - Indicador visual (barra ou gauge) do score
   - Consumir `GET /api/v1/fiscal-ai/risk-dashboard` (endpoint ja existe)
   - Tratar caso de zero notas importadas (exibir estado vazio)

#### Parte B - Modelo de Configuracoes da Loja

2. **Backend - Criar modelo `ConfiguracaoLoja`:**
   - Arquivo: `backend/app/models/configuracao_loja.py`
   - Campos:
     - `id` (PK)
     - `regime_tributario` (enum: 'simples_nacional', 'regime_normal')
     - `uf` (sigla com 2 caracteres: SP, RJ, MG, etc.)
     - `margem_minima_percentual` (float, default 0.05)
     - `aliquota_impostos_default` (float, opcional)
     - `updated_at` (timestamp)
   - Singleton: so deve existir 1 registro (ou usar a ultima)

3. **Backend - Criar endpoints CRUD:**
   - Arquivo: `backend/app/api/v1/configuracoes.py`
   - `GET /api/v1/configuracoes/loja` - retorna configuracao atual
   - `PUT /api/v1/configuracoes/loja` - atualiza configuracao
   - Autenticacao obrigatoria

4. **Backend - Integrar nos fluxos fiscais:**
   - `ocr.py`: ler `regime_tributario` e `uf` das configuracoes para passar
     ao `auditar_nota_fiscal()` em vez de `None`
   - `pdv_service.py`: ler `margem_minima_percentual` das configuracoes em
     vez do hardcoded `0.05`

5. **Criar migracao Alembic:**
   ```bash
   alembic revision --autogenerate -m "20260321_configuracao_loja"
   ```

6. **Frontend - Tela de configuracoes (opcional nesta iteracao):**
   - Pagina ou modal simples em Configuracoes com campos de regime, UF e margem
   - Pode ser adicionada em task futura se necessario

7. **Testes:**
   - Teste do endpoint GET/PUT de configuracoes
   - Teste de que a auditoria fiscal usa regime da configuracao
   - Teste de que o PDV usa margem da configuracao

### Criterio de aceite

- Dashboard exibe card de saude fiscal com dados reais.
- Modelo `ConfiguracaoLoja` criado com migracao.
- Endpoints GET/PUT funcionais e autenticados.
- Auditoria fiscal e PDV leem parametros da configuracao.
- Testes passando.

### Branch sugerida

`feat/dashboard-fiscal-configuracao-loja`
