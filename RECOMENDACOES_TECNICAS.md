# Recomendacoes Tecnicas Unificadas - Loja Project

## Objetivo
Consolidar em um unico plano as recomendacoes ja levantadas anteriormente com as novas sugestoes recebidas, com foco em **confiabilidade**, **seguranca**, **performance** e **escalabilidade**.

---

##  Alta Prioridade (executar primeiro)

### 1) Testes automatizados para fluxos criticos
**Por que:** reduzir regressoes e dar seguranca para refatoracoes.

**Escopo minimo inicial:**
- Autenticacao (`/api/v1/users/token`, `/api/v1/users/me`)
- Estoque v2 (`/api/v2/estoque`, `/api/v2/estoque/transacao`)
- OCR assincrono (criacao de tarefa e consulta de status)

**Recomendacao pratica:**
- Criar suite com `pytest` + `httpx` + `pytest-asyncio`
- Definir gate de CI para impedir merge com testes falhando
- Meta incremental: 60% inicial  80% nos modulos criticos

---

### 2) Seguranca de autenticacao e CORS
**Por que:** evitar inconsistencia de autenticacao e configuracao insegura em producao.

**Acoes:**
- Padronizar `tokenUrl` em todos os pontos para `/api/v1/users/token`
- Corrigir autenticacao opcional com `auto_error=False`
- Restringir `CORS_ORIGINS` por ambiente (dev/staging/prod)
- Impedir `allow_credentials=True` com wildcard em producao

---

### 3) Gestao de segredos e variaveis de ambiente
**Por que:** prevenir vazamento de credenciais e falhas em runtime.

**Acoes:**
- Garantir `.env` fora do versionamento (com `.env.example` versionado)
- Validar campos obrigatorios no startup (ja existe base para isso)
- Trocar placeholders sensiveis por instrucoes explicitas de seguranca na documentacao
- Revisar `.gitignore` para remover ruidos e duplicacoes

---

### 4) Tratamento centralizado de erros
**Por que:** padronizar respostas de erro e evitar exposicao de detalhes internos.

**Acoes:**
- Adicionar exception handlers globais no FastAPI
- Criar formato unico de erro (`code`, `message`, `details`, `trace_id`)
- Mapear excecoes de negocio (ex.: estoque insuficiente) para respostas consistentes

---

##  Media Prioridade (qualidade e operacao)

### 5) Otimizacao de performance no estoque (N+1)
**Por que:** endpoints degradam com crescimento de produtos/transacoes.

**Acoes:**
- Refatorar listagem para query agregada com `JOIN` + subquery/window function
- Medir benchmark antes/depois (tempo de resposta e numero de queries)

---

### 6) Rate limiting em OCR e LLM
**Por que:** proteger endpoints caros contra abuso e sobrecarga.

**Acoes:**
- Introduzir limiter (ex.: `slowapi`)
- Aplicar limites por IP e por usuario autenticado
- Definir limites distintos para OCR upload e chamadas LLM

---

### 7) Logging estruturado e observabilidade
**Por que:** facilitar troubleshooting, auditoria e operacao em producao.

**Acoes:**
- Padronizar logging em JSON (ou formato estruturado equivalente)
- Inserir `request_id`/`trace_id` por requisicao
- Medir metricas basicas (latencia, erros por endpoint, filas OCR)

---

### 8) Docker Compose para desenvolvimento e onboarding
**Por que:** reduzir friccao de setup e diferencas de ambiente.

**Acoes:**
- Versionar `docker-compose.yml` com API + PostgreSQL
- Opcionalizar servicos pesados (OCR/LLM) por profiles
- Incluir comandos de bootstrap no README

---

### 9) Paginacao consistente
**Por que:** evitar payloads excessivos e manter padrao de API.

**Acoes:**
- Padronizar paginacao (`limit/offset` ou cursor)
- Retornar metadados (`total`, `page`, `next`, `prev`) nos endpoints listaveis

---

##  Arquitetura e crescimento (medio/longo prazo)

### 10) Desacoplamento do pipeline OCR  LLM  cadastro
**Por que:** melhorar robustez, escalabilidade e rastreabilidade operacional.

**Acoes:**
- Migrar para fila assincrona (Celery + Redis / ARQ)
- Persistir estado da tarefa fora da memoria do processo
- Adicionar idempotencia, retry e TTL de tarefas

---

### 11) Evolucao de autenticacao com refresh token
**Por que:** melhorar UX e seguranca em sessoes longas.

**Acoes:**
- Implementar `/refresh` com refresh token rotativo
- Access token curto (ex.: 15 min) + refresh de maior duracao (ex.: 7 dias)
- Estrategia de revogacao e blacklist para logout/comprometimento

---

### 12) Estrategia explicita de versionamento de API
**Por que:** reduzir ambiguidade de endpoints legados e evitar quebra de clientes.

**Acoes:**
- Definir politica oficial (v1 legado, v2 ativo, cronograma de depreciacao)
- Documentar claramente endpoints estaveis vs legados
- Padronizar novas features na versao ativa

---

### 13) Convergencia para arquitetura async no banco
**Por que:** alinhar implementacao com direcao tecnica documentada.

**Acoes:**
- Plano incremental para `AsyncEngine` / `AsyncSession`
- Comecar por modulos de maior I/O (OCR/estoque)
- Garantir cobertura de testes antes da migracao por modulo

---

### 14) Desacoplamento de dependencias pesadas
**Por que:** reduzir tempo de build e custo operacional do core.

**Acoes:**
- Separar dependencias OCR/ML do core (ex.: `requirements-ocr.txt`)
- Manter instalacao minima para API base

---

 ##  Modulos de Negocio (Status atual)

 - [x] **Cadastro de Fornecedores:** CNPJ, contato, prazo de pagamento
 - [x] **Cadastro de Clientes:** Nome, telefone, tipo (varejo/atacado)
 - [x] **Categorias Hierarquicas:** Ex: Fios > Cabo 2.5mm
 - [x] **Precificacao Avancada:** Custo, Varejo, Atacado (multiplos precos)
 - [x] **Unidades de Medida:** Venda por metro ou unidade
 - [x] **PDV (Ponto de Venda):** Registro de venda com baixa automatica
 - [x] **Orcamentos:** Criacao e conversao automatica em venda
- [x] **Contas a Receber:** Parcelamento e acompanhamento de valores pendentes
 - [x] **Financeiro:** Controle de caixa diario (abertura/fechamento)
 - [x] **Relatorios:** Estoque baixo, Vendas por periodo
- [x] **Dashboard:** Alertas de estoque para operacao diaria

 ---

 ##  Frontend (Telas Planejadas)

 - [ ] **Login:** Autenticacao segura
 - [ ] **Dashboard:** Resumo do dia (vendas, alertas)
 - [ ] **PDV:** Interface agil para caixa
 - [ ] **Cadastros:** Grids para Produtos, Fornecedores, Clientes
 - [ ] **Estoque:** Consulta rapida e movimentacao
 - [ ] **Orcamentos:** Editor de orcamentos
 - [ ] **Relatorios:** Visualizacao de dados

 ---

 ## Plano sugerido de execucao (6 passos)

1. **Passo 1 e passo 2:** testes criticos + seguranca (auth/CORS/segredos) + erro global
2. **Passo 3:** performance estoque + paginacao consistente
3. **Passo 4:**  rate limiting + logging estruturado
4. **Passo 5:** docker compose + split de dependencias OCR/ML
5. **Passo 6:** desenho tecnico de OCR em fila + refresh token + politica de versionamento API

---

## Status de execucao (inicio das melhorias)

-  **Documentacao atualizada:** plano convertido para passos (passo 1, passo 2, etc.).
-  **Incremento concluido:** gate de CI configurado para rodar testes criticos de backend a cada push/PR.
-  **Incremento concluido:** suite de testes criticos expandida para cobrir OCR assincrono com cenario de erro e recuperacao.
-  **Incremento concluido:** gate de CI atualizado com cenarios criticos de OCR assincrono (erro/recuperacao e status de tarefa inexistente).
-  **Incremento concluido:** validacoes automatizadas adicionadas para CORS por ambiente e `tokenUrl` padronizado em autenticacao.
-  **Incremento concluido:** Passo 2 finalizado com fortalecimento da gestao de segredos, validacoes de startup e revisao de `.env.example`.
-  **Incremento concluido:** Passo 4 finalizado com rate limiting consistente em toda a API e logging estruturado observavel em eventos criticos.
-  **Proximo incremento:** relatorios basicos (estoque baixo, vendas por periodo).

---

## Criterios de sucesso (KPIs)

- Cobertura de testes dos modulos criticos  80%
- Reducao de queries no endpoint de estoque completo
- Zero uso de CORS wildcard com credenciais em producao
- Disponibilidade do OCR sem perda de tarefas em restart
- Tempo de setup de ambiente dev reduzido (com compose)
