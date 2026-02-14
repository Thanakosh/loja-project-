# Guia de Migração v1.0 → v2.0

Este documento fornece instruções detalhadas para migrar seu sistema da versão 1.0 para a versão 2.0 do Loja Project.

---

## 📋 Visão Geral das Mudanças

A versão 2.0 introduz mudanças significativas na arquitetura do sistema, focando em escalabilidade, performance e rastreabilidade. As principais áreas afetadas são:

1. **Sistema de Estoque**: Migração para modelo baseado em transações
2. **Dependências**: Atualização para Pydantic v2 e FastAPI mais recente
3. **Autenticação**: Implementação obrigatória de JWT em todos os endpoints
4. **OCR**: Processamento assíncrono para evitar timeouts
5. **LLM**: Integração inteligente para análise de notas fiscais

---

## 🔧 Pré-requisitos

Antes de iniciar a migração, certifique-se de:

- Fazer **backup completo do banco de dados**
- Ter Python 3.11+ instalado
- Ter acesso ao servidor PostgreSQL
- Ter credenciais de administrador do sistema

---

## 📦 Passo 1: Atualizar Dependências

### 1.1 Atualizar requirements.txt

O arquivo `requirements.txt` foi completamente atualizado. As principais mudanças são:

```diff
- fastapi>=0.68.0,<0.69.0
+ fastapi>=0.104.0,<0.105.0

- pydantic>=1.8.0,<2.0.0
+ pydantic>=2.5.0,<3.0.0

+ aiofiles>=23.2.0  # Nova dependência para OCR assíncrono
```

### 1.2 Instalar novas dependências

```bash
cd backend
pip install -r requirements.txt --upgrade
```

**Atenção**: A atualização do Pydantic pode causar conflitos. Recomenda-se usar um ambiente virtual limpo.

---

## 🗄️ Passo 2: Migrar Banco de Dados

### 2.1 Fazer Backup

```bash
pg_dump -U postgres -d loja_db > backup_pre_migration_$(date +%Y%m%d).sql
```

### 2.2 Executar Migrações Alembic

```bash
cd /path/to/loja-project
alembic upgrade head
```

A migração `refactor_estoque_v2` irá:

1. Criar tabela `transacao_estoque`
2. Migrar dados existentes de `produto.quantidade` para transações
3. Adicionar campos `ativo` e `estoque_minimo` em `produto`
4. Criar índices para otimização
5. Renomear tabela `users` para `user` (se necessário)

### 2.3 Verificar Migração

```sql
-- Verificar se a tabela foi criada
SELECT COUNT(*) FROM transacao_estoque;

-- Verificar se os dados foram migrados
SELECT p.id, p.nome, COUNT(t.id) as num_transacoes
FROM produto p
LEFT JOIN transacao_estoque t ON p.id = t.produto_id
GROUP BY p.id, p.nome;
```

---

## 💻 Passo 3: Atualizar Código da Aplicação

### 3.1 Schemas Pydantic

**Antes (v1):**
```python
class ProdutoRead(ProdutoBase):
    id: int
    
    class Config:
        orm_mode = True
```

**Depois (v2):**
```python
from pydantic import ConfigDict

class ProdutoRead(ProdutoBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
```

### 3.2 Serialização de Modelos

**Antes (v1):**
```python
db_produto = Produto(**produto.dict())
```

**Depois (v2):**
```python
db_produto = Produto(**produto.model_dump())
```

### 3.3 Validadores

**Antes (v1):**
```python
from pydantic import validator

@validator("DATABASE_URL", pre=True)
def validate_database_url(cls, v: str) -> str:
    ...
```

**Depois (v2):**
```python
from pydantic import field_validator

@field_validator("DATABASE_URL")
@classmethod
def validate_database_url(cls, v: str) -> str:
    ...
```

---

## 🔐 Passo 4: Implementar Autenticação

### 4.1 Criar Usuário Inicial

Execute o script para criar um usuário administrador:

```python
from app.core.security import get_password_hash
from app.models.user import User
from app.core.database import SessionLocal

db = SessionLocal()

admin = User(
    email="admin@loja.com",
    hashed_password=get_password_hash("senha_segura_123"),
    full_name="Administrador",
    is_active=True,
    is_superuser=True,
    is_verified=True
)

db.add(admin)
db.commit()
print(f"Usuário criado: {admin.email}")
```

### 4.2 Obter Token JWT

```bash
curl -X POST "http://localhost:8000/api/v1/users/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@loja.com&password=senha_segura_123"
```

### 4.3 Atualizar Clientes da API

Todos os clientes devem incluir o token JWT no header:

```bash
curl -X GET "http://localhost:8000/api/v1/produtos" \
  -H "Authorization: Bearer <seu_token_jwt>"
```

---

## 📊 Passo 5: Migrar Sistema de Estoque

### 5.1 Entender o Novo Modelo

**Antes (v1)**: Quantidade armazenada diretamente no produto

```python
produto = Produto(nome="Produto A", quantidade=100)
```

**Depois (v2)**: Quantidade calculada a partir de transações

```python
# Criar produto
produto = Produto(nome="Produto A")

# Registrar entrada inicial
transacao = TransacaoEstoque(
    produto_id=produto.id,
    tipo=TipoTransacao.ENTRADA,
    quantidade=100,
    motivo="Estoque inicial"
)
```

### 5.2 Usar Nova API de Estoque

**Endpoint legado (ainda funcional):**
```
GET /api/v1/estoque
```

**Novo endpoint (recomendado):**
```
GET /api/v2/estoque
POST /api/v2/estoque/transacao
GET /api/v2/estoque/produto/{id}
GET /api/v2/estoque/historico/{id}
```

### 5.3 Exemplo de Uso

```python
import requests

# Autenticar
token = "seu_token_jwt"
headers = {"Authorization": f"Bearer {token}"}

# Registrar saída de estoque
transacao = {
    "produto_id": 1,
    "tipo": "SAIDA",
    "quantidade": -10,  # Negativo para saída
    "motivo": "Venda #123"
}

response = requests.post(
    "http://localhost:8000/api/v2/estoque/transacao",
    json=transacao,
    headers=headers
)

print(response.json())
```

---

## 🖼️ Passo 6: Migrar Processamento de OCR

### 6.1 Usar Endpoint Assíncrono

**Antes (v1):**
```python
# Upload síncrono (pode causar timeout)
files = {"file": open("nota.jpg", "rb")}
response = requests.post("http://localhost:8000/api/v1/ocr/upload", files=files)
texto = response.json()["texto"]
```

**Depois (v2):**
```python
# Upload assíncrono
files = {"file": open("nota.jpg", "rb")}
response = requests.post(
    "http://localhost:8000/api/v1/ocr/upload",
    files=files,
    params={"use_llm": True},  # Usar LLM para análise inteligente
    headers=headers
)

task_id = response.json()["task_id"]

# Consultar status
import time
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/v1/ocr/status/{task_id}",
        headers=headers
    )
    status = status_response.json()
    
    if status["status"] == "completed":
        resultado = status["result"]
        break
    elif status["status"] == "failed":
        print(f"Erro: {status['error']}")
        break
    
    time.sleep(2)  # Aguardar 2 segundos
```

---

## 🤖 Passo 7: Integrar LLM para Notas Fiscais

### 7.1 Configurar Ollama (Opcional)

Se você deseja usar processamento local:

```bash
# Instalar Ollama
curl https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull gemma:3b
```

### 7.2 Usar Análise Inteligente

```python
# Processar nota fiscal completa
files = {"file": open("nota_fiscal.jpg", "rb")}
response = requests.post(
    "http://localhost:8000/api/v1/ocr/processar-nota-fiscal",
    files=files,
    params={"auto_cadastrar": True},  # Cadastrar produtos automaticamente
    headers=headers
)

task_id = response.json()["task_id"]

# Aguardar processamento...
# O resultado incluirá NotaFiscalExtraida com todos os produtos
```

---

## ✅ Passo 8: Validar Migração

### 8.1 Checklist de Validação

- [ ] Banco de dados migrado sem erros
- [ ] Todos os produtos têm transações iniciais
- [ ] Estoque calculado corretamente
- [ ] Autenticação funcionando
- [ ] OCR assíncrono processando imagens
- [ ] LLM extraindo dados corretamente
- [ ] Endpoints legados ainda funcionais

### 8.2 Testes Recomendados

```bash
# 1. Testar autenticação
curl -X POST "http://localhost:8000/api/v1/users/token" \
  -d "username=admin@loja.com&password=senha"

# 2. Testar listagem de produtos
curl -X GET "http://localhost:8000/api/v1/produtos" \
  -H "Authorization: Bearer <token>"

# 3. Testar estoque
curl -X GET "http://localhost:8000/api/v2/estoque" \
  -H "Authorization: Bearer <token>"

# 4. Testar transação
curl -X POST "http://localhost:8000/api/v2/estoque/transacao" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"produto_id": 1, "tipo": "ENTRADA", "quantidade": 50, "motivo": "Teste"}'
```

---

## 🚨 Problemas Comuns

### Erro: "Could not validate credentials"

**Causa**: Token JWT inválido ou expirado

**Solução**: Obter novo token via `/api/v1/users/token`

### Erro: "Estoque insuficiente"

**Causa**: Tentativa de saída maior que estoque disponível

**Solução**: Verificar estoque atual antes de registrar saída

### Erro: "Pydantic validation error"

**Causa**: Schemas incompatíveis entre v1 e v2

**Solução**: Atualizar código do cliente para usar novos schemas

### Erro: "Table 'transacao_estoque' doesn't exist"

**Causa**: Migração não executada

**Solução**: Executar `alembic upgrade head`

---

## 🔄 Rollback (Se Necessário)

Se encontrar problemas críticos, você pode reverter para v1:

```bash
# 1. Restaurar banco de dados
psql -U postgres -d loja_db < backup_pre_migration_YYYYMMDD.sql

# 2. Reverter migração
alembic downgrade -1

# 3. Reinstalar dependências antigas
pip install -r requirements_v1.txt
```

---

## 📞 Suporte

Se encontrar problemas durante a migração:

1. Consulte o [CHANGELOG.md](./CHANGELOG.md) para detalhes das mudanças
2. Verifique os logs da aplicação
3. Abra uma issue no repositório GitHub

---

**Boa sorte com a migração! 🚀**
