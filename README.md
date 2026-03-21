# Loja Project

Sistema de Gerenciamento Comercial para pequenos e medios negocios.

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

##  Visao Geral

O **Loja Project** e uma solucao de backend desenvolvida com **FastAPI**, voltada para gestao comercial com controle de estoque, PDV, orcamentos, clientes, fornecedores e importacao de notas fiscais via XML de NFe.

###  Status da v2.1.0

- **Importacao de NFe via XML**: caminho oficial de entrada fiscal no sistema
- **PDV com baixa automatica de estoque**: operacao de venda integrada ao estoque
- **Orcamentos com conversao em venda**: fluxo comercial completo
- **Contas a receber com parcelamento**: suporte para vendas a prazo
- **Relatorios operacionais**: vendas por periodo e estoque baixo
- **Dashboard com alertas de estoque**
- **Autenticacao JWT** em toda a API protegida

---

##  Tecnologias

### Backend
- **Framework:** Python 3.12+ | FastAPI 0.109+ | Pydantic v2
- **Servidor:** Uvicorn com suporte assincrono

### Banco de Dados
- **ORM:** SQLAlchemy 2.0
- **SGBD:** PostgreSQL
- **Migracoes:** Alembic

### Frontend
- **UI:** React 18+ com TailwindCSS + TypeScript
- **Desktop:** Electron
- **Build Tool:** Vite

### Seguranca
- **Autenticacao:** JWT (python-jose)
- **Hash:** Bcrypt (passlib)
- **Validacao:** Pydantic v2

---

##  Funcionalidades

###  Implementadas

#### 1. Gestao de Estoque
- Sistema baseado em transacoes (ENTRADA, SAIDA, AJUSTE, DEVOLUCAO)
- Calculo dinamico de estoque
- Historico completo de movimentacoes
- Alertas de estoque baixo

#### 2. Importacao de Notas Fiscais (XML)
- Upload de XML de NFe com extracao automatica de produtos
- Auto-cadastro de fornecedor pelo CNPJ
- Revisao e edicao dos itens antes de importar
- Cadastro automatico de produtos com estoque inicial

#### 3. Modulo de Produtos
- CRUD completo com soft delete
- Estoque calculado dinamicamente
- Rastreamento de fornecedores e NCM

#### 4. PDV e Vendas
- Frente de caixa com baixa automatica de estoque
- Orcamentos com conversao em venda
- Contas a receber para pagamentos a prazo

#### 5. Cadastros
- Clientes e Fornecedores com validacao de CPF/CNPJ
- Notas Fiscais com historico e filtros por periodo

#### 6. Autenticacao e Seguranca
- JWT com expiracao configuravel
- Protecao de todos os endpoints
- Rate limiting por endpoint
- Logging estruturado em JSON

---

##  Em desenvolvimento (roadmap)

- **OCR de imagens e PDFs via IA (Gemini)** - **Fase 2 (TASK-011 adiada)**
- **Controle de caixa diario** (abertura/fechamento)
- **Categorias hierarquicas de produtos**
- **Precificacao atacado/varejo**
- **Camada de Inteligencia Fiscal com IA (proposta avaliada)** - ver `docs/PROPOSTA_CAMADA_INTELIGENCIA_FISCAL.md`

---

##  Instalacao

### Pre-requisitos

- Python 3.12+
- PostgreSQL 14+

### 1. Clonar o repositorio

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

### 3. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

#### Perfil opcional OCR/ML

Para habilitar dependencias pesadas de OCR/IA em ambientes que precisem desses recursos:

```bash
cd backend
pip install -r requirements-ocr.txt
```

> O perfil `requirements-ocr.txt` e opcional e separado do core para manter o setup base mais leve.

### 4. Configurar variaveis de ambiente

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

### 5. Criar banco e executar migracoes

```bash
createdb loja_db
alembic upgrade head
```

### 6. Criar usuario administrador

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

##  Versionamento da API

| Versao | Status | Uso |
|--------|--------|-----|
| `v1` | **Legado** (manutencao corretiva) | Endpoints existentes sem novas features |
| `v2` | **Ativo** (versao oficial) | Todas as novas funcionalidades |

>  `/api/v1/estoque` esta **depreciado** - use `/api/v2/estoque`. Consulte [docs/POLITICA_VERSIONAMENTO_API.md](docs/POLITICA_VERSIONAMENTO_API.md) para o cronograma completo.

---

##  Exemplos de uso da API

### Autenticacao

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

### Registrar entrada de estoque (v2 - ativo)

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

> Observacao: na versao 2.1.0, o upload aceita apenas XML de NFe como fluxo oficial.

---

##  Modelo de dados principal

```

   Produto    TransacaoEstoque    User

 id                    produto_id (FK)            id
 nome                  tipo (enum)                email
 fornecedor            quantidade                 password
 preco_*               motivo
 ativo                 usuario_id (FK)
 estoque_min           data_transacao



  estoque_atual (calculado dinamicamente)
```

---

##  Testes

```bash
cd backend
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov-report=html
```

---

##  Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para historico detalhado de mudancas.

---

##  Licenca

Este projeto esta sob a licenca MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

##  Autores

- **Thanakosh** - [@Thanakosh](https://github.com/Thanakosh)

---

**Desenvolvido com  e **
