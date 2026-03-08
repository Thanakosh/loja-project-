# Loja Project 🚀

Sistema de Gerenciamento Comercial para pequenos e médios negócios.

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## 🌟 Visão Geral

O **Loja Project** é uma solução de backend desenvolvida com **FastAPI**, voltada para gestão comercial com controle de estoque, PDV, orçamentos, clientes, fornecedores e importação de notas fiscais via XML de NFe.

### ✨ Status da v2.1.0

- **Importação de NFe via XML**: caminho oficial de entrada fiscal no sistema
- **PDV com baixa automática de estoque**: operação de venda integrada ao estoque
- **Orçamentos com conversão em venda**: fluxo comercial completo
- **Contas a receber com parcelamento**: suporte para vendas a prazo
- **Relatórios operacionais**: vendas por período e estoque baixo
- **Dashboard com alertas de estoque**
- **Autenticação JWT** em toda a API protegida

---

## 🛠️ Tecnologias

### Backend
- **Framework:** Python 3.12+ | FastAPI 0.109+ | Pydantic v2
- **Servidor:** Uvicorn com suporte assíncrono

### Banco de Dados
- **ORM:** SQLAlchemy 2.0
- **SGBD:** PostgreSQL
- **Migrações:** Alembic

### Frontend
- **UI:** React 18+ com TailwindCSS + TypeScript
- **Desktop:** Electron
- **Build Tool:** Vite

### Segurança
- **Autenticação:** JWT (python-jose)
- **Hash:** Bcrypt (passlib)
- **Validação:** Pydantic v2

---

## 📋 Funcionalidades

### ✅ Implementadas

#### 1. Gestão de Estoque
- Sistema baseado em transações (ENTRADA, SAIDA, AJUSTE, DEVOLUCAO)
- Cálculo dinâmico de estoque
- Histórico completo de movimentações
- Alertas de estoque baixo

#### 2. Importação de Notas Fiscais (XML)
- Upload de XML de NFe com extração automática de produtos
- Auto-cadastro de fornecedor pelo CNPJ
- Revisão e edição dos itens antes de importar
- Cadastro automático de produtos com estoque inicial

#### 3. Módulo de Produtos
- CRUD completo com soft delete
- Estoque calculado dinamicamente
- Rastreamento de fornecedores e NCM

#### 4. PDV e Vendas
- Frente de caixa com baixa automática de estoque
- Orçamentos com conversão em venda
- Contas a receber para pagamentos a prazo

#### 5. Cadastros
- Clientes e Fornecedores com validação de CPF/CNPJ
- Notas Fiscais com histórico e filtros por período

#### 6. Autenticação e Segurança
- JWT com expiração configurável
- Proteção de todos os endpoints
- Rate limiting por endpoint
- Logging estruturado em JSON

---

## 🔮 Em desenvolvimento (roadmap)

- **OCR de imagens e PDFs via IA (Gemini)** — **Fase 2 (TASK-011 adiada)**
- **Controle de caixa diário** (abertura/fechamento)
- **Categorias hierárquicas de produtos**
- **Precificação atacado/varejo**
- **Camada de Inteligência Fiscal com IA (proposta avaliada)** — ver `docs/PROPOSTA_CAMADA_INTELIGENCIA_FISCAL.md`

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.12+
- PostgreSQL 14+

### 1. Clonar o repositório

```bash
git clone https://github.com/Thanakosh/loja-project-.git
cd loja-project-
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

### 3. Instalar dependências

```bash
cd backend
pip install -r requirements.txt
```

#### Perfil opcional OCR/ML

Para habilitar dependências pesadas de OCR/IA em ambientes que precisem desses recursos:

```bash
cd backend
pip install -r requirements-ocr.txt
```

> O perfil `requirements-ocr.txt` é opcional e separado do core para manter o setup base mais leve.

### 4. Configurar variáveis de ambiente

Copie o exemplo e ajuste:

```bash
cp .env.example .env
```

Edite o `.env` com os valores reais:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/loja_db
JWT_SECRET=gere_uma_chave_segura_aqui
ENVIRONMENT=development
DEBUG=False
CORS_ORIGINS=["http://localhost:5173"]
```

> Gere uma chave segura com: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 5. Criar banco e executar migrações

```bash
createdb loja_db
alembic upgrade head
```

### 6. Criar usuário administrador

```bash
python create_user.py
```

### 7. Iniciar o servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:
- **API**: http://localhost:8000
- **Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔢 Versionamento da API

| Versão | Status | Uso |
|--------|--------|-----|
| `v1` | **Legado** (manutenção corretiva) | Endpoints existentes sem novas features |
| `v2` | **Ativo** (versão oficial) | Todas as novas funcionalidades |

> ⚠️ `/api/v1/estoque` está **depreciado** — use `/api/v2/estoque`. Consulte [docs/POLITICA_VERSIONAMENTO_API.md](docs/POLITICA_VERSIONAMENTO_API.md) para o cronograma completo.

---

## 📖 Exemplos de uso da API

### Autenticação

```bash
curl -X POST "http://localhost:8000/api/v1/users/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@loja.com&password=sua_senha"
```

### Listar produtos

```bash
GET /api/v1/produtos
Authorization: Bearer <token>
```

### Registrar entrada de estoque (v2 — ativo)

```bash
POST /api/v2/estoque/transacao
Authorization: Bearer <token>
Content-Type: application/json

{
  "produto_id": 1,
  "tipo": "ENTRADA",
  "quantidade": 100,
  "motivo": "Compra de fornecedor"
}
```

### Importar nota fiscal (XML)

```bash
POST /api/v1/ocr/upload-arquivo
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: nota_fiscal.xml
```

> Observação: na versão 2.1.0, o upload aceita apenas XML de NFe como fluxo oficial.

---

## 📊 Modelo de dados principal

```
┌─────────────┐         ┌──────────────────┐         ┌──────────┐
│   Produto   │◄────────│ TransacaoEstoque │────────►│   User   │
├─────────────┤         ├──────────────────┤         ├──────────┤
│ id          │         │ produto_id (FK)  │         │ id       │
│ nome        │         │ tipo (enum)      │         │ email    │
│ fornecedor  │         │ quantidade       │         │ password │
│ preco_*     │         │ motivo           │         └──────────┘
│ ativo       │         │ usuario_id (FK)  │
│ estoque_min │         │ data_transacao   │
└─────────────┘         └──────────────────┘
       │
       ▼
  estoque_atual (calculado dinamicamente)
```

---

## 🧪 Testes

```bash
cd backend
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov-report=html
```

---

## 📝 Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico detalhado de mudanças.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Autores

- **Thanakosh** - [@Thanakosh](https://github.com/Thanakosh)

---

**Desenvolvido com ❤️ e ☕**
