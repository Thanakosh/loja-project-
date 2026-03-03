# AGENTS.md — Guia de Operação para IAs

> Este arquivo é lido automaticamente por agentes de IA (Codex, Cursor, Claude, Copilot, etc.).
> **Siga estas regras antes de qualquer ação no repositório.**

---

## 🗂️ Visão Geral do Projeto

**Loja Project** é um sistema de gerenciamento comercial com backend em FastAPI + PostgreSQL.
Versão atual: `2.1.0` | Branch principal: `main`

```
loja-project-/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # Endpoints REST
│   │   ├── core/          # Config, database, security
│   │   ├── models/        # Modelos SQLAlchemy
│   │   └── schemas/       # Schemas Pydantic v2
│   ├── tests/             # Testes automatizados
│   └── requirements.txt   # Dependências principais
├── migrations/            # Migrações Alembic
├── checkpoints/           # Snapshots de estado do projeto
├── docs/                  # Documentação
├── AGENTS.md              # ← Este arquivo (leia sempre primeiro)
├── frontend/              # (Novo) Aplicação Desktop/Web React + Electron
├── CHANGELOG.md           # Histórico de versões
├── STRATEGY.md            # Direção técnica de longo prazo
└── RECOMENDACOES_TECNICAS.md  # Backlog técnico priorizado
```

---

## ⚙️ Stack e Versões Obrigatórias

| Tecnologia       | Versão mínima | Observação                          |
|------------------|---------------|-------------------------------------|
| Python           | 3.12          | Ambiente do Codex usa 3.12          |
| FastAPI          | >=0.109.0     | Não fixar versão exata              |
| Pydantic         | >=2.6.4       | **v2 obrigatório** — sem v1         |
| SQLAlchemy       | >=2.0.27      | Async engine disponível             |
| Alembic          | ==1.13.1      | Fixado — não alterar                |
| ollama (client)  | >=0.4.7       | Compatível com httpx>=0.26.0        |
| httpx            | >=0.26.0      | Não reduzir esta versão             |

## 🎨 Stack Frontend (Novo)

| Tecnologia       | Versão        | Finalidade                          |
|------------------|---------------|-------------------------------------|
| React            | 18+           | Interface de usuário (UI)           |
| Electron         | Latest        | Desktop App (Windows/Linux)         |
| Vite             | Latest        | Build tool e Dev Server             |
| TailwindCSS      | 3.4+          | Estilização (obrigatório)           |
| React Query      | Latest        | State management server-side        |
| Shadcn/ui        | Latest        | (Recomendado) Componentes UI        |

**⚠️ Regra de Ouro do Frontend:**
> **NUNCA DUPLICAR REGRAS DE NEGÓCIO NO FRONTEND.**
> O frontend deve ser apenas uma camada de visualização e interação.
> Cálculos de impostos, validações complexas e regras de estoque ficam **exclusivamente no Backend**.

---

## 🚦 Regras de Branch

| Branch                              | Finalidade                                 | Quem usa          |
|-------------------------------------|--------------------------------------------|-------------------|
| `main`                              | Código estável e revisado                  | Merge após revisão|
| `codex/<descricao-curta>`           | Tarefas do OpenAI Codex                    | Codex             |
| `cursor/<descricao-curta>`          | Tarefas do Cursor                          | Cursor            |
| `claude/<descricao-curta>`          | Tarefas do Claude                          | Claude            |
| `frontend/<descricao-curta>`        | Features de UI (React/Electron)            | Qualquer agente   |
| `feature/<descricao-curta>`         | Novas funcionalidades (Backend/Geral)      | Humano            |
| `fix/<descricao-curta>`             | Correções de bugs                          | Qualquer agente   |

**Regras:**
- ❌ Nunca commitar diretamente na `main`
- ✅ Sempre criar branch antes de qualquer alteração
- ✅ Um PR por tarefa — escopo pequeno e focado
- ✅ Resolver conflitos de merge antes do push

---

## 📝 Padrão de Commits

Use o padrão **Conventional Commits**:

```
<tipo>(<escopo>): <descrição curta em português>

[corpo opcional explicando o porquê]
```

| Tipo       | Quando usar                                      |
|------------|--------------------------------------------------|
| `feat`     | Nova funcionalidade                              |
| `fix`      | Correção de bug                                  |
| `refactor` | Refatoração sem mudança de comportamento         |
| `test`     | Adição ou correção de testes                     |
| `docs`     | Alterações em documentação                       |
| `chore`    | Tarefas de manutenção (deps, config, etc.)       |
| `perf`     | Melhoria de performance                          |

**Exemplos:**
```
feat(estoque): adiciona endpoint de entrada em lote
fix(auth): corrige validação de token expirado
chore(deps): atualiza ollama para >=0.4.7
test(produto): adiciona testes de criação com estoque inicial
```

---

## 🔒 Regras de Segurança — CRÍTICO

1. **Nunca commitar arquivos `.env`** — já está no `.gitignore`
2. **Usar `.env.example`** como referência de variáveis (sem valores reais)
3. **Nunca hardcodar** secrets, senhas ou tokens no código
4. **`test.db`** não deve ir para o repositório — adicionar ao `.gitignore` se necessário
5. **CORS:** nunca usar `["*"]` com `allow_credentials=True` em produção

---

## 🐍 Padrões de Código Python

### Schemas Pydantic
```python
# ✅ CORRETO — Pydantic v2
from pydantic import BaseModel, ConfigDict, field_validator

class MeuSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("campo")
    @classmethod
    def validar_campo(cls, v):
        return v

# ❌ ERRADO — Pydantic v1 (não usar)
class MeuSchema(BaseModel):
    class Config:
        orm_mode = True

    @validator("campo")
    def validar_campo(cls, v):
        return v
```

### Serialização de modelos
```python
# ✅ CORRETO
dados = schema.model_dump()
dados = schema.model_dump(exclude_unset=True)

# ❌ ERRADO
dados = schema.dict()
```

### Endpoints
```python
# ✅ CORRETO — sempre requer autenticação
@router.get("/", response_model=List[MeuSchema])
def listar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    ...
```

### Estoque
```python
# ✅ CORRETO — usar sistema de transações (v2)
# Endpoint: POST /api/v2/estoque/transacao

# ❌ EVITAR — campo quantidade direto no produto (legado v1)
produto.quantidade = 100
```

---

## 🗄️ Banco de Dados e Migrações

- **Nunca alterar tabelas manualmente** — sempre via Alembic
- **Sempre criar migração** ao adicionar/alterar modelos:
  ```bash
  alembic revision --autogenerate -m "descricao_da_mudanca"
  alembic upgrade head
  ```
- **Nomear arquivos de migração** com data: `YYYYMMDD_descricao.py`
- **Não deletar migrações antigas** — histório deve ser preservado

---

## 🧪 Testes

- Localização: `backend/tests/`
- Framework: `pytest` + `pytest-asyncio` + `httpx`
- Banco de testes: SQLite em memória (configurado em `conftest.py`)
- **Sempre adicionar testes** para novas features nos módulos críticos:
  - Autenticação
  - Estoque v2
  - OCR (criação e status de tarefa)

```bash
# Rodar testes
cd backend
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 📦 Dependências

- **Arquivo principal:** `backend/requirements.txt`
- **Dependências OCR/ML:** `backend/requirements-ocr.txt` (instalar separado)
- **Ao adicionar dependência:**
  1. Verificar conflitos com as existentes antes de adicionar
  2. Usar `>=versao` (sem fixar exato) salvo casos específicos
  3. Nunca reduzir versão de `httpx` abaixo de `>=0.26.0`
  4. Documentar no commit o motivo da adição
- **⚠️ bcrypt:** usar `==4.0.1` — a versão 5.x quebra compatibilidade com passlib 1.7.4 no Python 3.13 (erro: *password cannot be longer than 72 bytes*)

---

## 📋 Documentos de Referência

| Arquivo                      | Finalidade                                           | Atualizar quando?              |
|------------------------------|------------------------------------------------------|--------------------------------|
| `AGENTS.md`                  | Regras para IAs (este arquivo)                       | Quando mudar padrões do projeto|
| `CHANGELOG.md`               | Histórico de versões no formato Keep a Changelog     | A cada release                 |
| `STRATEGY.md`                | Direção técnica e arquitetural de longo prazo        | A cada mudança de direção      |
| `RECOMENDACOES_TECNICAS.md`  | Backlog de melhorias priorizadas (🔴🟡🟢)            | Ao concluir ou adicionar itens |
| `MIGRATION_GUIDE.md`         | Guia de migração entre versões                       | A cada breaking change         |

---

## ✅ Checklist antes do Push

- [ ] Estou em uma branch correta (não `main`)
- [ ] Sem marcadores de conflito (`<<<<<<<`, `=======`, `>>>>>>>`) em nenhum arquivo
- [ ] Sem arquivos `.env` ou secrets no commit
- [ ] Pydantic v2 em todos os schemas novos/editados (`model_dump`, `ConfigDict`)
- [ ] Dependências novas não conflitam com as existentes
- [ ] Testes passando localmente (`pytest tests/ -v`)
- [ ] Commit segue o padrão Conventional Commits
- [ ] `CHANGELOG.md` atualizado se for uma feature ou fix relevante

---

## ❓ Dúvidas sobre o projeto

Consulte nesta ordem:
1. Este arquivo (`AGENTS.md`)
2. `STRATEGY.md` — para decisões arquiteturais
3. `RECOMENDACOES_TECNICAS.md` — para o backlog de melhorias
4. `CHANGELOG.md` — para entender o histórico de decisões
