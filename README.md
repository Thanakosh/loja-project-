# Loja Project 🚀

Sistema de Gerenciamento Comercial Inteligente focado em automação, IA e produtividade para pequenos e médios negócios.

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## 🌟 Visão Geral

O **Loja Project** é uma solução de backend robusta desenvolvida com **FastAPI**, que integra ferramentas de **OCR (Reconhecimento Óptico de Caracteres)** e **Inteligência Artificial (LLMs)** para transformar processos manuais em fluxos de trabalho automatizados.

### ✨ Novidades da v2.0

- **Sistema de Transações de Estoque**: Rastreabilidade completa de movimentações
- **OCR Assíncrono**: Processamento em background para imagens grandes
- **Análise Inteligente com LLM**: Extração automática de dados de notas fiscais
- **Autenticação JWT**: Segurança em todos os endpoints
- **Performance 2-5x melhor**: Migração para Pydantic v2

---

## 🛠️ Tecnologias Principais

### Backend
- **Framework:** Python 3.11+ | FastAPI 0.104+ | Pydantic v2
- **Servidor:** Uvicorn com suporte assíncrono

### Banco de Dados
- **ORM:** SQLAlchemy 2.0 (async)
- **SGBD:** PostgreSQL
- **Migrações:** Alembic

### Inteligência Artificial
- **OCR:** EasyOCR (português)
- **LLM:** Ollama | Open Interpreter
- **Modelos:** Gemma 3B (local) | OpenAI-compatible APIs

### Segurança
- **Autenticação:** JWT (python-jose)
- **Hash:** Bcrypt (passlib)
- **Validação:** Pydantic v2

---

## 📋 Funcionalidades

### ✅ Implementadas

#### 1. Gestão de Estoque Avançada
- Sistema baseado em transações (ENTRADA, SAIDA, AJUSTE, DEVOLUCAO)
- Cálculo dinâmico de estoque
- Histórico completo de movimentações
- Alertas de estoque baixo
- Entrada em lote (notas fiscais)

#### 2. OCR de Notas Fiscais
- Processamento assíncrono (evita timeouts)
- Extração de texto com EasyOCR
- Análise inteligente com LLM
- Sistema de tarefas com consulta de status
- Cadastro automático de produtos

#### 3. Integração com LLM
- Análise de notas fiscais via IA
- Extração estruturada de dados
- Suporte a Ollama (local) e APIs externas
- Chat para análise de dados comerciais

#### 4. Módulo de Produtos
- CRUD completo
- Soft delete (campo `ativo`)
- Estoque calculado dinamicamente
- Rastreamento de fornecedores e NCM

#### 5. Módulo de Orçamentos
- Criação e acompanhamento
- Controle de status
- Vínculo com clientes
- Base para geração de PDF (próxima versão)

#### 6. Autenticação e Segurança
- JWT com expiração configurável
- Proteção de todos os endpoints
- Auditoria de transações por usuário
- Documentação Swagger com autenticação

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.11+
- PostgreSQL 14+
- (Opcional) Ollama para LLM local

### 1. Clonar Repositório

```bash
git clone https://github.com/Thanakosh/loja-project-.git
cd loja-project-
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

### 3. Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

Se for usar OCR (upload de imagens), instale também o pacote opcional de OCR/ML:

```bash
pip install -r requirements-ocr.txt
```

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/loja_db
SQLALCHEMY_ECHO=False

# Security
JWT_SECRET=sua_chave_secreta_muito_segura_aqui
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI (Opcional)
OLLAMA_URL=http://localhost:11434
OPEN_INTERPRETER_URL=http://localhost:4000/v1/chat/completions

# API Settings
DEBUG=False
CORS_ORIGINS=["http://localhost:3000"]
```

### 5. Criar Banco de Dados

```bash
createdb loja_db
```

### 6. Executar Migrações

```bash
alembic upgrade head
```

### 7. Criar Usuário Administrador

```python
python -c "
from app.core.security import get_password_hash
from app.models.user import User
from app.core.database import SessionLocal

db = SessionLocal()
admin = User(
    email='admin@loja.com',
    hashed_password=get_password_hash('admin123'),
    full_name='Administrador',
    is_active=True,
    is_superuser=True,
    is_verified=True
)
db.add(admin)
db.commit()
print('Usuário admin criado!')
"
```

### 8. Iniciar Servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:
- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📖 Uso da API

### Autenticação

```bash
# Obter token
curl -X POST "http://localhost:8000/api/v1/users/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@loja.com&password=admin123"

# Usar token nas requisições
curl -X GET "http://localhost:8000/api/v1/produtos" \
  -H "Authorization: Bearer <seu_token>"
```

### Exemplos de Endpoints

#### Listar Produtos
```bash
GET /api/v1/produtos
Authorization: Bearer <token>
```

#### Criar Produto
```bash
POST /api/v1/produtos
Authorization: Bearer <token>
Content-Type: application/json

{
  "nome": "Produto Exemplo",
  "fornecedor": "Fornecedor XYZ",
  "preco_unitario": 10.50,
  "preco_liquido": 9.00,
  "estoque_minimo": 10
}
```

#### Registrar Transação de Estoque
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

#### Processar Nota Fiscal com OCR
```bash
POST /api/v1/ocr/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <arquivo_imagem>
use_llm: true
```

---

## 📊 Arquitetura do Sistema

### Modelo de Dados

```
┌─────────────┐         ┌──────────────────┐         ┌──────────┐
│   Produto   │◄────────│ TransacaoEstoque │────────►│   User   │
├─────────────┤         ├──────────────────┤         ├──────────┤
│ id          │         │ id               │         │ id       │
│ nome        │         │ produto_id (FK)  │         │ email    │
│ fornecedor  │         │ tipo (enum)      │         │ password │
│ preco_*     │         │ quantidade       │         │ ...      │
│ ativo       │         │ motivo           │         └──────────┘
│ estoque_min │         │ usuario_id (FK)  │
└─────────────┘         │ data_transacao   │
                        └──────────────────┘

       │                       │
       │                       │
       ▼                       ▼
  estoque_atual          Histórico de
   (calculado)           movimentações
```

### Fluxo de Processamento de Nota Fiscal

```
1. Upload de imagem → OCR (EasyOCR) → Texto extraído
                              │
                              ▼
2. Texto → LLM (Ollama/OpenAI) → Dados estruturados
                              │
                              ▼
3. Validação → Cadastro de produtos → Transações de estoque
```

---

## 🔄 Migração da v1.0

Se você está atualizando de uma versão anterior, consulte o [**Guia de Migração**](MIGRATION_GUIDE.md) completo.

**Principais mudanças:**
- Pydantic v2 (breaking changes)
- Sistema de transações de estoque
- Autenticação obrigatória
- OCR assíncrono

---

## 🧪 Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio httpx

# Executar testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov-report=html
```

---

## 📈 Roadmap

### Curto Prazo (1-2 meses)
- [ ] Testes automatizados (cobertura >80%)
- [ ] Geração de PDF para orçamentos
- [ ] Docker Compose para deploy
- [ ] CI/CD com GitHub Actions

### Médio Prazo (3-6 meses)
- [ ] Integração WhatsApp Business
- [ ] Dashboard gerencial com gráficos
- [ ] Previsão de estoque com IA
- [ ] Relatórios personalizados

### Longo Prazo (6-12 meses)
- [ ] Frontend React/Vue.js
- [ ] App mobile (React Native)
- [ ] Multi-tenancy
- [ ] Marketplace de integrações

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📝 Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico detalhado de mudanças.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Autores

- **Thanakosh** - *Desenvolvimento inicial* - [@Thanakosh](https://github.com/Thanakosh)

---

## 🙏 Agradecimentos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - OCR de código aberto
- [Ollama](https://ollama.ai/) - LLMs locais
- Comunidade Python Brasil

---

**Desenvolvido com ❤️ e ☕ focando em eficiência e tecnologia de ponta.**
