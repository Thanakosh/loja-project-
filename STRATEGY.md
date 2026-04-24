# Estrategia de Desenvolvimento - Loja Project

Este documento consolida a direcao tecnica e de produto do sistema com base no
estado real do repositorio.

## 1. Estado tecnico consolidado

### Backend

- **Pydantic v2, FastAPI atual e SQLAlchemy 2.0** ja fazem parte da base
  principal do projeto.
- **Camada HTTP e acesso a banco em async** foram convergidos para
  `AsyncSession` / `get_async_db`, com validacao complementar em PostgreSQL
  real.
- **Cadeia Alembic** foi reforcada para bootstrap em banco PostgreSQL vazio,
  sem depender de `Base.metadata.create_all()`.
- **Seguranca e observabilidade** contam com validacoes de startup, CORS por
  ambiente, rate limiting, logging estruturado e `trace_id`.

### Frontend e desktop

- **Frontend React + Vite + TailwindCSS** esta operacional para os principais
  fluxos de negocio.
- **React Query** centraliza cache e mutacoes por dominio.
- **Electron Forge** esta configurado para empacotamento desktop Windows.
- **Playwright** cobre smoke tests de UI e um fluxo integrado real de PDV com
  backend e PostgreSQL.

## 2. Direcao de produto

### Core comercial (entregue)

O nucleo operacional do ERP ja esta implementado e deve ser tratado como base
estavel de evolucao:

- produtos, clientes, fornecedores e usuarios
- categorias hierarquicas
- unidades de medida
- precificacao avancada (custo, varejo, atacado)
- estoque v2 transacional
- PDV com baixa automatica
- orcamentos com conversao em venda
- contas a receber
- caixa diario
- relatorios operacionais e dashboard

### Fiscal e inteligencia operacional (entregue parcialmente)

O caminho fiscal ativo hoje e focado em XML de NFe e inteligencia deterministica
ou assistida, sem reabrir OCR generico prematuramente:

- importacao oficial de XML de NFe
- listagem e detalhamento de notas fiscais
- payload fiscal interno normalizado e versionado
- motor deterministico de custo e preco minimo
- auditoria fiscal, feedback, dashboard de risco e classificacao NCM

Ainda permanecem fora do escopo entregue:

- emissao de NF-e / NFC-e
- contas a pagar
- comunicacao externa por WhatsApp

### OCR e IA de documentos (Fase 2)

- **Status atual:** OCR de imagens e PDFs esta desativado nesta linha.
- **Direcao futura:** so retomar com fila persistente, retry, idempotencia e
  rastreabilidade operacional adequadas.
- **Regra de produto:** manter XML de NFe como fluxo fiscal oficial enquanto a
  Fase 2 nao estiver estruturada.

## 3. Infraestrutura e DevOps

Os pilares operacionais principais ja foram estabelecidos:

- `docker-compose.yml` para desenvolvimento
- workflow de CI para testes criticos de backend
- workflow de E2E de frontend com smoke tests e job integrado real
- workflow de build desktop Windows com instalador `.exe` e checksum
- gate de validacao em instalacao limpa documentado e executado

As melhorias de infraestrutura que seguem relevantes sao:

- evoluir builds Docker para estrategia multi-stage mais enxuta
- refinar cache e tempo de pipeline
- amadurecer o handoff de release desktop

## 4. Proximas frentes prioritarias

1. **Expandir versionamento v2 da API**
   - Promover novos modulos para `/api/v2` sem reabrir contratos antigos em
     `v1`.

2. **Evoluir a frente fiscal e financeira**
   - Planejar emissao de NF-e/NFC-e e contas a pagar como proximos blocos de
     produto, sem acoplar isso ao fluxo atual de XML de NFe.

3. **Refinar UX e componentes de forma incremental**
   - O design system ja foi inicializado; novas telas e alteracoes relevantes
     devem reaproveitar os componentes padronizados.

4. **Integracao WhatsApp para orcamentos**
   - Manter como frente posterior, dependente de numero dedicado, credenciais e
     validacao operacional real.

5. **Retomar OCR/PDF apenas com arquitetura robusta**
   - Fila persistente, observabilidade, retries e estado de tarefa fora da
     memoria do processo.

## 5. Resumo executivo

- O projeto ja deixou de ser apenas uma base de backend e hoje opera como
  plataforma full-stack.
- A fundacao tecnica principal esta pronta: async, migrations, seguranca,
  testes, frontend e desktop.
- O foco agora deve sair de "construir infraestrutura basica" e migrar para
  "aumentar cobertura real, consistencia de UX e amadurecer releases".
