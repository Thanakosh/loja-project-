# AGENTS.md - Guia de Operacao para IAs

> Este arquivo e lido automaticamente por agentes de IA (Codex, Cursor, Claude, Copilot, etc.).
> **Siga estas regras antes de qualquer acao no repositorio.**

---

##  Visao Geral do Projeto

**Loja Project** e um sistema de gerenciamento comercial com backend em FastAPI + PostgreSQL.
Versao atual: `2.1.0` | Branch principal: `main`

```
loja-project-/
 backend/
    app/
       api/v1/        # Endpoints REST
       core/          # Config, database, security
       models/        # Modelos SQLAlchemy
       schemas/       # Schemas Pydantic v2
    tests/             # Testes automatizados
    requirements.txt   # Dependencias principais
 migrations/            # Migracoes Alembic
 checkpoints/           # Snapshots de estado do projeto
 docs/                  # Documentacao
 AGENTS.md              #  Este arquivo (leia sempre primeiro)
 frontend/              # (Novo) Aplicacao Desktop/Web React + Electron
 CHANGELOG.md           # Historico de versoes
 STRATEGY.md            # Direcao tecnica de longo prazo
 RECOMENDACOES_TECNICAS.md  # Backlog tecnico priorizado
```

---

##  Stack e Versoes Obrigatorias

| Tecnologia       | Versao minima | Observacao                          |
|------------------|---------------|-------------------------------------|
| Python           | 3.12          | Ambiente do Codex usa 3.12          |
| FastAPI          | >=0.109.0     | Nao fixar versao exata              |
| Pydantic         | >=2.6.4       | **v2 obrigatorio** - sem v1         |
| SQLAlchemy       | >=2.0.27      | Async engine disponivel             |
| Alembic          | ==1.13.1      | Fixado - nao alterar                |
| httpx            | >=0.26.0      | Nao reduzir esta versao             |

##  Stack Frontend (Novo)

| Tecnologia       | Versao        | Finalidade                          |
|------------------|---------------|-------------------------------------|
| React            | 18+           | Interface de usuario (UI)           |
| Electron         | Latest        | Desktop App (Windows/Linux)         |
| Vite             | Latest        | Build tool e Dev Server             |
| TailwindCSS      | 3.4+          | Estilizacao (obrigatorio)           |
| React Query      | Latest        | State management server-side        |
| Shadcn/ui        | Latest        | (Recomendado) Componentes UI        |

** Regra de Ouro do Frontend:**
> **NUNCA DUPLICAR REGRAS DE NEGOCIO NO FRONTEND.**
> O frontend deve ser apenas uma camada de visualizacao e interacao.
> Calculos de impostos, validacoes complexas e regras de estoque ficam **exclusivamente no Backend**.

---

##  Regras de Branch

| Branch                              | Finalidade                                 | Quem usa          |
|-------------------------------------|--------------------------------------------|-------------------|
| `main`                              | Codigo estavel e revisado                  | Merge apos revisao|
| `codex/<descricao-curta>`           | Tarefas do OpenAI Codex                    | Codex             |
| `cursor/<descricao-curta>`          | Tarefas do Cursor                          | Cursor            |
| `claude/<descricao-curta>`          | Tarefas do Claude                          | Claude            |
| `frontend/<descricao-curta>`        | Features de UI (React/Electron)            | Qualquer agente   |
| `feature/<descricao-curta>`         | Novas funcionalidades (Backend/Geral)      | Humano            |
| `fix/<descricao-curta>`             | Correcoes de bugs                          | Qualquer agente   |

**Regras:**
-  Nunca commitar diretamente na `main`
-  Sempre criar branch antes de qualquer alteracao
-  Um PR por tarefa - escopo pequeno e focado
-  Resolver conflitos de merge antes do push

---

##  Padrao de Commits

Use o padrao **Conventional Commits**:

```
<tipo>(<escopo>): <descricao curta em portugues>

[corpo opcional explicando o porque]
```

| Tipo       | Quando usar                                      |
|------------|--------------------------------------------------|
| `feat`     | Nova funcionalidade                              |
| `fix`      | Correcao de bug                                  |
| `refactor` | Refatoracao sem mudanca de comportamento         |
| `test`     | Adicao ou correcao de testes                     |
| `docs`     | Alteracoes em documentacao                       |
| `chore`    | Tarefas de manutencao (deps, config, etc.)       |
| `perf`     | Melhoria de performance                          |

**Exemplos:**
```
feat(estoque): adiciona endpoint de entrada em lote
fix(auth): corrige validacao de token expirado
chore(deps): atualiza httpx para >=0.27.0
test(produto): adiciona testes de criacao com estoque inicial
```

---

##  Regras de Seguranca - CRITICO

1. **Nunca commitar arquivos `.env`** - ja esta no `.gitignore`
2. **Usar `.env.example`** como referencia de variaveis (sem valores reais)
3. **Nunca hardcodar** secrets, senhas ou tokens no codigo
4. **`test.db`** nao deve ir para o repositorio - adicionar ao `.gitignore` se necessario
5. **CORS:** nunca usar `["*"]` com `allow_credentials=True` em producao

---

##  Padroes de Codigo Python

### Schemas Pydantic
```python
#  CORRETO - Pydantic v2
from pydantic import BaseModel, ConfigDict, field_validator

class MeuSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("campo")
    @classmethod
    def validar_campo(cls, v):
        return v

#  ERRADO - Pydantic v1 (nao usar)
class MeuSchema(BaseModel):
    class Config:
        orm_mode = True

    @validator("campo")
    def validar_campo(cls, v):
        return v
```

### Serializacao de modelos
```python
#  CORRETO
dados = schema.model_dump()
dados = schema.model_dump(exclude_unset=True)

#  ERRADO
dados = schema.dict()
```

### Endpoints
```python
#  CORRETO - sempre requer autenticacao
@router.get("/", response_model=List[MeuSchema])
def listar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    ...
```

### Estoque
```python
#  CORRETO - usar sistema de transacoes (v2)
# Endpoint: POST /api/v2/estoque/transacao

#  EVITAR - campo quantidade direto no produto (legado v1)
produto.quantidade = 100
```

---

##  Banco de Dados e Migracoes

- **Nunca alterar tabelas manualmente** - sempre via Alembic
- **Sempre criar migracao** ao adicionar/alterar modelos:
  ```bash
  alembic revision --autogenerate -m "descricao_da_mudanca"
  alembic upgrade head
  ```
- **Nomear arquivos de migracao** com data: `YYYYMMDD_descricao.py`
- **Nao deletar migracoes antigas** - historio deve ser preservado
- **Revisar manualmente** toda migracao gerada por `--autogenerate` antes de commitar
- **Sempre verificar a chain** com `alembic history --verbose` antes de criar nova migracao

---

##  Testes

- Localizacao: `backend/tests/`
- Framework: `pytest` + `pytest-asyncio` + `httpx`
- Banco de testes: SQLite em memoria (configurado em `conftest.py`)
- **Sempre adicionar testes** para novas features nos modulos criticos:
  - Autenticacao
  - Estoque v2
  - OCR (criacao e status de tarefa)

```bash
# Rodar testes
cd backend
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

---

##  Dependencias

- **Arquivo principal:** `backend/requirements.txt`
- **Dependencias OCR/ML:** `backend/requirements-ocr.txt` (instalar separado)
- **Ao adicionar dependencia:**
  1. Verificar conflitos com as existentes antes de adicionar
  2. Usar `>=versao` (sem fixar exato) salvo casos especificos
  3. Nunca reduzir versao de `httpx` abaixo de `>=0.26.0`
  4. Documentar no commit o motivo da adicao
- ** bcrypt:** usar `==4.0.1` - a versao 5.x quebra compatibilidade com passlib 1.7.4 no Python 3.13 (erro: *password cannot be longer than 72 bytes*)

---

##  Documentos de Referencia

| Arquivo                      | Finalidade                                           | Atualizar quando              |
|------------------------------|------------------------------------------------------|--------------------------------|
| `AGENTS.md`                  | Regras para IAs (este arquivo)                       | Quando mudar padroes do projeto|
| `CHANGELOG.md`               | Historico de versoes no formato Keep a Changelog     | A cada release                 |
| `STRATEGY.md`                | Direcao tecnica e arquitetural de longo prazo        | A cada mudanca de direcao      |
| `RECOMENDACOES_TECNICAS.md`  | Backlog de melhorias priorizadas ()            | Ao concluir ou adicionar itens |
| `MIGRATION_GUIDE.md`         | Guia de migracao entre versoes                       | A cada breaking change         |

---

##  Checklist antes do Push

- [ ] Estou em uma branch correta (nao `main`)
- [ ] Sem marcadores de conflito (`<<<<<<<`, `=======`, `>>>>>>>`) em nenhum arquivo
- [ ] Sem arquivos `.env` ou secrets no commit
- [ ] Pydantic v2 em todos os schemas novos/editados (`model_dump`, `ConfigDict`)
- [ ] Dependencias novas nao conflitam com as existentes
- [ ] Testes passando localmente (`pytest tests/ -v`)
- [ ] Commit segue o padrao Conventional Commits
- [ ] `CHANGELOG.md` atualizado se for uma feature ou fix relevante

---

##  Duvidas sobre o projeto

Consulte nesta ordem:
1. Este arquivo (`AGENTS.md`)
2. `STRATEGY.md` - para decisoes arquiteturais
3. `RECOMENDACOES_TECNICAS.md` - para o backlog de melhorias
4. `CHANGELOG.md` - para entender o historico de decisoes
---

## Padrao de Tasks

Arquivos em `tasks/` devem manter o frontmatter YAML em ASCII puro.

Regras:
- usar `status` apenas como `pendente`, `concluida` ou `concluido`
- usar `priority` em texto simples, como `alta`, `media`, `baixa` ou `arquitetura`
- nao usar emojis no frontmatter
- evitar acentos e outros caracteres Unicode no frontmatter
- o corpo do arquivo pode permanecer em portugues normal quando necessario
