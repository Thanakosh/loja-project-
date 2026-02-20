# Recomendações Técnicas Unificadas — Loja Project

## Objetivo
Consolidar em um único plano as recomendações já levantadas anteriormente com as novas sugestões recebidas, com foco em **confiabilidade**, **segurança**, **performance** e **escalabilidade**.

---

## 🔴 Alta Prioridade (executar primeiro)

### 1) Testes automatizados para fluxos críticos
**Por que:** reduzir regressões e dar segurança para refatorações.

**Escopo mínimo inicial:**
- Autenticação (`/api/v1/users/token`, `/api/v1/users/me`)
- Estoque v2 (`/api/v2/estoque`, `/api/v2/estoque/transacao`)
- OCR assíncrono (criação de tarefa e consulta de status)

**Recomendação prática:**
- Criar suíte com `pytest` + `httpx` + `pytest-asyncio`
- Definir gate de CI para impedir merge com testes falhando
- Meta incremental: 60% inicial → 80% nos módulos críticos

---

### 2) Segurança de autenticação e CORS
**Por que:** evitar inconsistência de autenticação e configuração insegura em produção.

**Ações:**
- Padronizar `tokenUrl` em todos os pontos para `/api/v1/users/token`
- Corrigir autenticação opcional com `auto_error=False`
- Restringir `CORS_ORIGINS` por ambiente (dev/staging/prod)
- Impedir `allow_credentials=True` com wildcard em produção

---

### 3) Gestão de segredos e variáveis de ambiente
**Por que:** prevenir vazamento de credenciais e falhas em runtime.

**Ações:**
- Garantir `.env` fora do versionamento (com `.env.example` versionado)
- Validar campos obrigatórios no startup (já existe base para isso)
- Trocar placeholders sensíveis por instruções explícitas de segurança na documentação
- Revisar `.gitignore` para remover ruídos e duplicações

---

### 4) Tratamento centralizado de erros
**Por que:** padronizar respostas de erro e evitar exposição de detalhes internos.

**Ações:**
- Adicionar exception handlers globais no FastAPI
- Criar formato único de erro (`code`, `message`, `details`, `trace_id`)
- Mapear exceções de negócio (ex.: estoque insuficiente) para respostas consistentes

---

## 🟡 Média Prioridade (qualidade e operação)

### 5) Otimização de performance no estoque (N+1)
**Por que:** endpoints degradam com crescimento de produtos/transações.

**Ações:**
- Refatorar listagem para query agregada com `JOIN` + subquery/window function
- Medir benchmark antes/depois (tempo de resposta e número de queries)

---

### 6) Rate limiting em OCR e LLM
**Por que:** proteger endpoints caros contra abuso e sobrecarga.

**Ações:**
- Introduzir limiter (ex.: `slowapi`)
- Aplicar limites por IP e por usuário autenticado
- Definir limites distintos para OCR upload e chamadas LLM

---

### 7) Logging estruturado e observabilidade
**Por que:** facilitar troubleshooting, auditoria e operação em produção.

**Ações:**
- Padronizar logging em JSON (ou formato estruturado equivalente)
- Inserir `request_id`/`trace_id` por requisição
- Medir métricas básicas (latência, erros por endpoint, filas OCR)

---

### 8) Docker Compose para desenvolvimento e onboarding
**Por que:** reduzir fricção de setup e diferenças de ambiente.

**Ações:**
- Versionar `docker-compose.yml` com API + PostgreSQL
- Opcionalizar serviços pesados (OCR/LLM) por profiles
- Incluir comandos de bootstrap no README

---

### 9) Paginação consistente
**Por que:** evitar payloads excessivos e manter padrão de API.

**Ações:**
- Padronizar paginação (`limit/offset` ou cursor)
- Retornar metadados (`total`, `page`, `next`, `prev`) nos endpoints listáveis

---

## 🟢 Arquitetura e crescimento (médio/longo prazo)

### 10) Desacoplamento do pipeline OCR → LLM → cadastro
**Por que:** melhorar robustez, escalabilidade e rastreabilidade operacional.

**Ações:**
- Migrar para fila assíncrona (Celery + Redis / ARQ)
- Persistir estado da tarefa fora da memória do processo
- Adicionar idempotência, retry e TTL de tarefas

---

### 11) Evolução de autenticação com refresh token
**Por que:** melhorar UX e segurança em sessões longas.

**Ações:**
- Implementar `/refresh` com refresh token rotativo
- Access token curto (ex.: 15 min) + refresh de maior duração (ex.: 7 dias)
- Estratégia de revogação e blacklist para logout/comprometimento

---

### 12) Estratégia explícita de versionamento de API
**Por que:** reduzir ambiguidade de endpoints legados e evitar quebra de clientes.

**Ações:**
- Definir política oficial (v1 legado, v2 ativo, cronograma de depreciação)
- Documentar claramente endpoints estáveis vs legados
- Padronizar novas features na versão ativa

---

### 13) Convergência para arquitetura async no banco
**Por que:** alinhar implementação com direção técnica documentada.

**Ações:**
- Plano incremental para `AsyncEngine` / `AsyncSession`
- Começar por módulos de maior I/O (OCR/estoque)
- Garantir cobertura de testes antes da migração por módulo

---

### 14) Desacoplamento de dependências pesadas
**Por que:** reduzir tempo de build e custo operacional do core.

**Ações:**
- Separar dependências OCR/ML do core (ex.: `requirements-ocr.txt`)
- Manter instalação mínima para API base

---
 
 ## 🛒 Módulos de Negócio (Pendentes)
 
 - [x] **Cadastro de Fornecedores:** CNPJ, contato, prazo de pagamento
 - [ ] **Cadastro de Clientes:** Nome, telefone, tipo (varejo/atacado)
 - [ ] **Categorias Hierárquicas:** Ex: Fios > Cabo 2.5mm²
 - [ ] **Precificação Avançada:** Custo, Varejo, Atacado (múltiplos preços)
 - [ ] **Unidades de Medida:** Venda por metro ou unidade
 - [ ] **PDV (Ponto de Venda):** Registro de venda com baixa automática
 - [ ] **Orçamentos:** Criação e conversão automática em venda
 - [ ] **Financeiro:** Controle de caixa diário (abertura/fechamento)
 - [ ] **Relatórios:** Estoque baixo, Vendas por período
 
 ---
 
 ## 🖥️ Frontend (Telas Planejadas)
 
 - [ ] **Login:** Autenticação segura
 - [ ] **Dashboard:** Resumo do dia (vendas, alertas)
 - [ ] **PDV:** Interface ágil para caixa
 - [ ] **Cadastros:** Grids para Produtos, Fornecedores, Clientes
 - [ ] **Estoque:** Consulta rápida e movimentação
 - [ ] **Orçamentos:** Editor de orçamentos
 - [ ] **Relatórios:** Visualização de dados
 
 ---
 
 ## Plano sugerido de execução (6 passos)

1. **Passo 1 e passo 2:** testes críticos + segurança (auth/CORS/segredos) + erro global
2. **Passo 3:** performance estoque + paginação consistente
3. **Passo 4:** ✅ rate limiting + logging estruturado
4. **Passo 5:** docker compose + split de dependências OCR/ML
5. **Passo 6:** desenho técnico de OCR em fila + refresh token + política de versionamento API

---

## Status de execução (início das melhorias)

- ✅ **Documentação atualizada:** plano convertido para passos (passo 1, passo 2, etc.).
- ✅ **Incremento concluído:** gate de CI configurado para rodar testes críticos de backend a cada push/PR.
- ✅ **Incremento concluído:** suíte de testes críticos expandida para cobrir OCR assíncrono com cenário de erro e recuperação.
- ✅ **Incremento concluído:** gate de CI atualizado com cenários críticos de OCR assíncrono (erro/recuperação e status de tarefa inexistente).
- ✅ **Incremento concluído:** validações automatizadas adicionadas para CORS por ambiente e `tokenUrl` padronizado em autenticação.
- ✅ **Incremento concluído:** Passo 2 finalizado com fortalecimento da gestão de segredos, validações de startup e revisão de `.env.example`.
- ✅ **Incremento concluído:** Passo 4 finalizado com rate limiting consistente em toda a API e logging estruturado observável em eventos críticos.
- 🎯 **Próximo incremento:** módulo de PDV (Ponto de Venda).

---

## Critérios de sucesso (KPIs)

- Cobertura de testes dos módulos críticos ≥ 80%
- Redução de queries no endpoint de estoque completo
- Zero uso de CORS wildcard com credenciais em produção
- Disponibilidade do OCR sem perda de tarefas em restart
- Tempo de setup de ambiente dev reduzido (com compose)
