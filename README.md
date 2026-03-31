# Loja Project

Sistema de gerenciamento comercial para pequenos e medios negocios, com backend
FastAPI + PostgreSQL e frontend React/Electron para operacao web e desktop.

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## Visao Geral

O **Loja Project** evoluiu de um backend operacional para uma plataforma
full-stack de gestao comercial. Hoje o repositorio concentra:

- backend FastAPI com SQLAlchemy 2.0 assincrono e PostgreSQL
- frontend React + Vite + TailwindCSS + React Query
- empacotamento desktop com Electron Forge
- suites de teste para backend, smoke E2E de frontend e fluxo integrado real do
  PDV

### Estado atual da linha 2.1.x

- **Backend async validado em PostgreSQL real** com cadeia Alembic revisada para
  bootstrap em banco vazio
- **Estoque v2 transacional** como fluxo oficial, com depreciacao explicita do
  estoque legado em `v1`
- **PDV, Orcamentos, Contas a Receber e Caixa Diario** operando de forma
  integrada
- **Cadastros completos** de produtos, clientes, fornecedores e categorias
  hierarquicas
- **Precificacao avancada** com custo, varejo, atacado e regra de preco minimo
- **Importacao fiscal oficial via XML de NFe**, com payload fiscal normalizado e
  trilha de auditoria
- **Frontend operacional** para login, dashboard, PDV, estoque, produtos,
  clientes, fornecedores, orcamentos, relatorios, notas fiscais e configuracao
  da loja
- **Build desktop Windows** com pipeline, instalador `.exe`, checksum e gate de
  validacao em instalacao limpa

> OCR de imagens e PDFs segue desativado nesta linha. O caminho fiscal oficial
> ativo hoje e o XML de NFe.

---

## Tecnologias

### Backend

- **Framework:** Python 3.12+ | FastAPI 0.109+ | Pydantic v2
- **ORM:** SQLAlchemy 2.0 com `AsyncSession`
- **Driver:** `asyncpg` para runtime PostgreSQL
- **Migracoes:** Alembic

### Frontend e Desktop

- **UI:** React 18 + TypeScript + TailwindCSS
- **Estado server-side:** React Query
- **Build:** Vite
- **Desktop:** Electron Forge
- **Testes E2E:** Playwright

### Seguranca e Observabilidade

- **Autenticacao:** JWT com refresh token rotativo
- **Protecoes:** rate limiting, validacao de startup e CORS por ambiente
- **Rastreabilidade:** `trace_id` por requisicao e logging estruturado

---

## Funcionalidades Implementadas

### 1. Operacao comercial

- Cadastro completo de produtos, clientes, fornecedores e usuarios
- Categorias hierarquicas para produtos
- Unidades de medida e multiplos precos por produto
- Politica de desconto e validacao de preco minimo no PDV
- Configuracao da loja e dashboard operacional/fiscal

### 2. Estoque, vendas e financeiro

- Estoque baseado em transacoes (`ENTRADA`, `SAIDA`, `AJUSTE`, `DEVOLUCAO`)
- Calculo dinamico de saldo e historico completo de movimentacoes
- PDV com baixa automatica de estoque e bloqueio sem caixa aberto
- Orcamentos com itens, conversao em venda e cancelamento
- Contas a receber com parcelamento
- Controle de caixa diario com abertura, fechamento e historico
- Relatorios operacionais de vendas e estoque baixo

### 3. Fiscal

- Importacao de XML de NFe com extracao de produtos, fornecedor e campos
  fiscais por item
- Notas fiscais com listagem, filtros e detalhamento de itens
- Payload fiscal interno normalizado e versionado para consumo por modulos
  internos
- Motor deterministico de custo e preco minimo
- Endpoints de auditoria fiscal, classificacao NCM, dashboard de risco e
  feedback operacional

### 4. Frontend e Desktop

- Telas para login, dashboard, produtos, estoque, clientes, fornecedores,
  orcamentos, vendas, PDV, caixa, relatorios, importacao de nota, notas fiscais
  e configuracoes
- Hooks React Query por dominio para cache, invalidacao e mutacoes
- Suite Playwright de smoke tests e fluxo integrado real do PDV com backend
  PostgreSQL
- Empacotamento Windows via Electron Forge com workflow de CI dedicado

### 5. Qualidade operacional

- Contrato padronizado de erros com `code`, `message`, `details` e `trace_id`
- Testes de backend para modulos criticos e baseline alta de cobertura
- Validacao do runtime async em PostgreSQL real com runner dedicado
- CI para backend, E2E de frontend e build desktop Windows

---

## Roadmap Atual

As principais frentes restantes hoje sao:

- expandir os testes E2E integrados reais para produtos, orcamentos e
  importacao de nota
- consolidar um design system reutilizavel no frontend
- integrar envio de orcamentos por WhatsApp
- continuar a promocao gradual de novos modulos para `/api/v2`
- retomar OCR de imagens e PDFs apenas com arquitetura de fila persistente
- evoluir a frente fiscal para emissao de NF-e/NFC-e e contas a pagar

---

## Instalacao Rapida

### Pre-requisitos

- Python 3.12+
- PostgreSQL 14+
- Node.js 20+

### 1. Clonar o repositorio

```bash
git clone https://github.com/Thanakosh/loja-project-.git
cd loja-project-
```

### 2. Configurar o backend

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

cd backend
pip install -r requirements.txt
```

> `requirements-ocr.txt` permanece separado do core e reservado para a futura
> retomada da Fase 2 de OCR/IA.

### 3. Configurar variaveis de ambiente

Copie o exemplo e ajuste os valores reais:

```bash
cp .env.example .env
```

Exemplo minimo:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/loja_db
JWT_SECRET=gere_uma_chave_segura_aqui
ENVIRONMENT=development
DEBUG=false
CORS_ORIGINS=["http://localhost:5173"]
```

### 4. Executar migracoes

```bash
alembic upgrade head
```

### 5. Subir a API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:

- **API:** http://localhost:8000
- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 6. Criar o primeiro usuario

Com a API rodando, registre um usuario inicial:

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@loja.com",
    "password": "admin123",
    "full_name": "Administrador",
    "is_superuser": true
  }'
```

### 7. Configurar o frontend web

```bash
cd frontend
npm install
cp .env.example .env
```

Defina `VITE_API_URL` no `.env`:

```env
VITE_API_URL=http://localhost:8000
```

Inicie o frontend:

```bash
npm run dev
```

Aplicacao disponivel em `http://localhost:5173`.

### 8. Build desktop Windows

```bash
cd frontend
npm run build
npm run make
```

O pipeline oficial de release desktop publica o instalador `.exe` e o checksum
SHA256 como artifacts.

### Ambiente demo opcional

Para gerar rapidamente um banco SQLite de demonstracao com dados de exemplo:

```bash
cd backend
python demo_seed.py
```

Esse fluxo cria `demo.db` com usuario `admin@loja.com / admin` e nao substitui
o setup com PostgreSQL.

---

## Versionamento da API

| Versao | Status | Uso |
|--------|--------|-----|
| `v1` | Ativo/legado por modulo | Manutencao corretiva e modulos ainda nao promovidos |
| `v2` | Ativo | Novas funcionalidades e modulos migrados |

Hoje, o modulo de estoque ja tem trilha ativa em `v2`:

- `POST /api/v2/estoque/transacao`
- `GET /api/v2/estoque`
- `GET /api/v2/estoque/produto/{id}`
- `GET /api/v2/estoque/historico/{id}`

Consulte [docs/POLITICA_VERSIONAMENTO_API.md](docs/POLITICA_VERSIONAMENTO_API.md)
para a politica completa.

---

## Testes

### Backend

```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term-missing
```

### Frontend

```bash
cd frontend
npm run test:e2e
npm run test:e2e:integrated
```

---

## Documentacao Complementar

- [CHANGELOG.md](CHANGELOG.md): historico de mudancas
- [STRATEGY.md](STRATEGY.md): direcao tecnica e de produto
- [RECOMENDACOES_TECNICAS.md](RECOMENDACOES_TECNICAS.md): backlog consolidado e
  prioridades
- [docs/POLITICA_VERSIONAMENTO_API.md](docs/POLITICA_VERSIONAMENTO_API.md):
  politica de versionamento da API
- [docs/releases/desktop-release-notes.md](docs/releases/desktop-release-notes.md):
  handoff da trilha desktop

---

## Licenca

Este projeto esta sob a licenca MIT. Veja [LICENSE](LICENSE) para detalhes.
