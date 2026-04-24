# Recomendacoes Tecnicas Unificadas - Loja Project

## Objetivo

Consolidar o backlog tecnico com foco no que ja foi entregue, no que ainda esta
aberto e no que vale investir a seguir.

---

## Situacao consolidada

A fundacao tecnica principal do projeto ja foi executada:

- testes criticos e gates de CI ativos
- seguranca de auth, CORS e segredos reforcada
- contrato centralizado de erros
- paginacao consistente e rate limiting
- logging estruturado com `trace_id`
- split de dependencias pesadas
- convergencia do backend para async com validacao real em PostgreSQL
- frontend operacional com React Query, smoke tests E2E e fluxo integrado real
- trilha desktop com Electron Forge, pipeline Windows e gate de instalacao limpa

O backlog abaixo passa a refletir esse estado, separando o que esta concluido do
que permanece como proxima prioridade.

---

## Recomendacoes estruturais ja concluídas

### 1) Testes automatizados para fluxos criticos
**Status atual:** concluido como base; expansao integrada continua desejavel.

Entregue:
- suites de backend para modulos criticos
- gate de CI para backend
- smoke tests E2E de frontend
- fluxos integrados reais de PDV, caixa, produtos, orcamentos e importacao de
  nota com backend e PostgreSQL

### 2) Seguranca de autenticacao e CORS
**Status atual:** concluido.

Entregue:
- `tokenUrl` padronizado
- validacoes de `ENVIRONMENT`, `CORS_ORIGINS` e `JWT_SECRET`
- bloqueios explicitos para configuracoes inseguras em startup

### 3) Gestao de segredos e variaveis de ambiente
**Status atual:** concluido.

Entregue:
- endurecimento de `.gitignore`
- alinhamento de `.env.example`
- validacoes de startup para placeholders e configuracoes invalidas

### 4) Tratamento centralizado de erros
**Status atual:** concluido.

Entregue:
- handlers globais
- formato padronizado de erro com `code`, `message`, `details` e `trace_id`
- migracao incremental de endpoints legados para excecoes de negocio

### 5) Otimizacao de performance no estoque (N+1)
**Status atual:** concluido.

Entregue:
- refatoracao das consultas principais do estoque
- benchmark documentado para comparacao antes/depois

### 6) Rate limiting em OCR e LLM
**Status atual:** concluido para endpoints relevantes.

Entregue:
- limiter aplicado de forma consistente em autenticacao e modulos principais
- cobertura automatizada para headers e limites por endpoint

### 7) Logging estruturado e observabilidade
**Status atual:** concluido.

Entregue:
- logging estruturado
- `trace_id` por requisicao
- testes para eventos criticos de autenticacao

### 8) Docker Compose para desenvolvimento e onboarding
**Status atual:** concluido.

Entregue:
- `docker-compose.yml` versionado no repositorio

### 9) Paginacao consistente
**Status atual:** concluido.

Entregue:
- padronizacao progressiva dos endpoints listaveis
- metadados de pagina nos modulos principais

### 10) Desacoplamento do pipeline OCR / LLM / cadastro
**Status atual:** adiado ate a retomada da Fase 2 de OCR.

Observacao:
- o fluxo ativo atual permanece em XML de NFe
- a fila persistente segue como pre-requisito para reativar OCR de imagem/PDF

### 11) Evolucao de autenticacao com refresh token
**Status atual:** concluido.

Entregue:
- endpoint de refresh token
- rotacao de refresh token
- logout com revogacao

### 12) Estrategia explicita de versionamento de API
**Status atual:** concluido como politica; adocao operacional segue por modulo.

Entregue:
- politica oficial documentada
- headers de deprecacao em estoque legado

### 13) Convergencia para arquitetura async no banco
**Status atual:** concluido.

Entregue:
- migracao do backend principal para `AsyncSession`
- validacao complementar em PostgreSQL real
- ajuste da chain Alembic para bootstrap em banco vazio

### 14) Desacoplamento de dependencias pesadas
**Status atual:** concluido.

Entregue:
- separacao entre `requirements.txt` e `requirements-ocr.txt`

---

## Modulos de negocio (status atual)

- [x] **Cadastro de Fornecedores:** CNPJ, contato, prazo de pagamento
- [x] **Cadastro de Clientes:** nome, telefone, tipo e integracao com frontend
- [x] **Categorias Hierarquicas:** arvore e filtro por subcategorias
- [x] **Precificacao Avancada:** custo, varejo, atacado e preco minimo
- [x] **Unidades de Medida:** suporte no cadastro e operacao
- [x] **PDV:** venda com baixa automatica e validacoes operacionais
- [x] **Orcamentos:** criacao, cancelamento e conversao em venda
- [x] **Contas a Receber:** parcelamento e acompanhamento de pendencias
- [x] **Financeiro:** caixa diario com abertura e fechamento
- [x] **Relatorios:** estoque baixo e vendas por periodo
- [x] **Dashboard:** alertas operacionais e visao fiscal
- [x] **Notas Fiscais:** listagem, filtros e detalhamento
- [x] **Validacao Fiscal de Entrada:** auditoria operacional de tributacao,
  CFOP, CST/CSOSN, NCM, CNPJ do fornecedor e conferencia de ICMS (`TASK-053`)
- [x] **Configuracao da Loja:** leitura e atualizacao por API e frontend
- [x] **WhatsApp para Orcamentos:** gateway separado, pareamento por QR,
  status de sessao e envio de PDF de orcamento. Validacao operacional com
  numero real permanece pendente.

---

## Frontend (telas disponiveis)

- [x] **Login**
- [x] **Dashboard**
- [x] **PDV**
- [x] **Produtos**
- [x] **Fornecedores**
- [x] **Clientes**
- [x] **Estoque**
- [x] **Orcamentos**
- [x] **Relatorios**
- [x] **Vendas**
- [x] **Notas Fiscais**
- [x] **Caixa Diario**
- [x] **Configuracoes da Loja**
- [x] **Importacao de Nota**

Estado atual do frontend:

- E2E integrado real cobre os fluxos principais de PDV, caixa, produtos,
  orcamentos, importacao de nota, Estoque operacional e alertas do Dashboard.
- O design system com `shadcn/ui` esta inicializado, documentado e adotado nas
  principais telas.
- A refatoracao de telas grandes segue como manutencao incremental quando
  houver mudanca funcional ou retrabalho visual relevante.

---

## Proximas prioridades recomendadas

### 1) Promocao gradual de modulos para `/api/v2`
**Por que:** a politica existe, mas a adocao completa ainda e parcial.

### 2) Evolucao fiscal e financeira
**Por que:** emissao de NF-e/NFC-e e contas a pagar continuam fora do escopo
entregue.

### 3) Refinamento incremental de UX e componentes
**Por que:** o design system ja existe; agora o retorno esta em aplicar os
componentes padronizados quando telas forem alteradas, sem abrir uma frente
grande so de refatoracao visual.

### 4) Validacao operacional do WhatsApp para orcamentos
**Por que:** a base tecnica ja foi entregue, mas ainda falta parear um numero
dedicado, enviar um PDF real e registrar evidencia operacional. Pode aguardar
ate haver credenciais e numero dedicado.

### 5) Retomar OCR de imagem/PDF com arquitetura robusta
**Por que:** o caminho antigo foi desativado corretamente; a volta deve ocorrer
com fila persistente e observabilidade. Deve permanecer adiado enquanto o XML
de NFe atender ao fluxo fiscal oficial.

---

## Criterios de sucesso (KPIs)

- Cobertura robusta dos modulos criticos e manutencao da cobertura integrada real
- Zero configuracao insegura de CORS com credenciais em producao
- Bootstrap Alembic confiavel em PostgreSQL vazio
- Releases desktop reproduziveis com checklist e evidencias
- Menor retrabalho visual no frontend com evolucao incremental do design system
