---
task_id: TASK-006
title: "Implementar paginacao consistente nos endpoints de listagem"
priority: media
scope: backend/app/ (schemas + endpoints de listagem)
branch: feat/paginacao-consistente
commit_message: "feat(api): implementa paginacao consistente com metadados em todos os endpoints de listagem"
estimated_effort: 25 minutos
status: concluida
---

# TASK-006: Implementar paginacao consistente nos endpoints de listagem

## Contexto

Atualmente os endpoints de listagem usam `skip`/`limit` simples, mas NAO retornam metadados
de paginacao (`total`, `page`, `pages`, etc.). O cliente nao sabe quantos itens existem no total
nem se ha mais paginas. Isso dificulta a criacao de um frontend com paginacao.

### Endpoints afetados
| Endpoint | Arquivo | Paginacao atual |
|----------|---------|-----------------|
| `GET /api/v1/produtos` | `produto.py` | `skip`/`limit` sem `total` |
| `GET /api/v1/orcamentos` | `orcamento.py` | Nenhuma (retorna tudo) |
| `GET /api/v2/estoque/` | `estoque_v2.py` | Nenhuma (retorna tudo) |
| `GET /api/v2/estoque/historico/{id}` | `estoque_v2.py` | `limite` sem `total` |
| `GET /api/v1/estoque` | `estoque.py` | Nenhuma (legado, nao alterar) |

## Passo 1: Criar schema generico de paginacao

### Criar arquivo `backend/app/schemas/pagination.py`

```python
from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema generico de resposta paginada."""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
```

### Atualizar `backend/app/schemas/__init__.py`

Adicionar ao import:
```python
from .pagination import PaginatedResponse
```

E ao `__all__`:
```python
"PaginatedResponse",
```

## Passo 2: Criar funcao helper de paginacao

### Adicionar ao final de `backend/app/core/database.py` (ou criar `backend/app/core/pagination.py`)

```python
from sqlalchemy.orm import Query
from math import ceil


def paginate(query: Query, page: int = 1, page_size: int = 50) -> dict:
    """
    Aplica paginacao a uma query SQLAlchemy e retorna dict com metadados.

    Args:
        query: SQLAlchemy Query object
        page: Numero da pagina (1-indexed)
        page_size: Itens por pagina

    Returns:
        dict com keys: items, total, page, page_size, pages
    """
    total = query.count()
    pages = ceil(total / page_size) if page_size > 0 else 0
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
```

## Passo 3: Atualizar endpoints

### 3a. `backend/app/api/v1/produto.py` - `listar_produtos`

```python
from ...schemas.pagination import PaginatedResponse
from ...core.pagination import paginate

@router.get("/", response_model=PaginatedResponse[ProdutoRead])
def listar_produtos(
    page: int = Query(1, ge=1, description="Numero da pagina"),
    page_size: int = Query(50, ge=1, le=200, description="Itens por pagina"),
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os produtos com paginacao (requer autenticacao)"""
    query = db.query(Produto)
    if not incluir_inativos:
        query = query.filter(Produto.ativo == True)
    return paginate(query, page=page, page_size=page_size)
```

> **Nota:** adicionar `from fastapi import Query` ao import se nao estiver presente.

### 3b. `backend/app/api/v1/orcamento.py` - `listar_orcamentos`

```python
from ...schemas.pagination import PaginatedResponse
from ...core.pagination import paginate
from fastapi import Query

@router.get("/", response_model=PaginatedResponse[OrcamentoRead])
def listar_orcamentos(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os orcamentos com paginacao (requer autenticacao)"""
    return paginate(db.query(Orcamento), page=page, page_size=page_size)
```

### 3c. `backend/app/api/v1/estoque_v2.py` - `obter_historico_produto`

```python
from ...schemas.pagination import PaginatedResponse
from ...core.pagination import paginate

@router.get("/historico/{produto_id}", response_model=PaginatedResponse[TransacaoEstoqueRead])
def obter_historico_produto(
    produto_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtem o historico de transacoes de um produto com paginacao"""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise ProdutoNaoEncontradoError()

    query = db.query(TransacaoEstoque)\
        .filter(TransacaoEstoque.produto_id == produto_id)\
        .order_by(TransacaoEstoque.data_transacao.desc())

    return paginate(query, page=page, page_size=page_size)
```

### 3d. `GET /api/v2/estoque/` - listagem de estoque
Este endpoint usa logica customizada (subquery + construcao manual de EstoqueAtual),
entao NAO usar o helper generico. Apenas adicionar os metadados manualmente:

```python
@router.get("/", response_model=PaginatedResponse[EstoqueAtual])
def listar_estoque_completo(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    apenas_ativos: bool = True,
    apenas_baixo: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # ... (mesma logica de query existente) ...

    # Ao final, paginar o resultado manualmente:
    total = len(resultado)
    pages = ceil(total / page_size) if page_size > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": resultado[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
```

> Adicionar `from math import ceil` ao import.

## Passo 4: Atualizar testes

Os testes existentes esperam uma **lista** como resposta. Agora os endpoints retornam
um **objeto** com `items`, `total`, etc. Atualizar os testes para acessar `.json()["items"]`
em vez de `.json()` diretamente.

Exemplo de ajuste:
```python
# ANTES
response = client.get("/api/v1/produtos/", headers=auth_headers)
assert isinstance(response.json(), list)

# DEPOIS
response = client.get("/api/v1/produtos/", headers=auth_headers)
data = response.json()
assert "items" in data
assert "total" in data
assert isinstance(data["items"], list)
```

## Formato da resposta paginada

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "pages": 3
}
```

## Passos
1. Criar branch `feat/paginacao-consistente`
2. Criar `backend/app/schemas/pagination.py`
3. Criar `backend/app/core/pagination.py` (helper)
4. Atualizar os 4 endpoints de listagem
5. Atualizar testes existentes para o novo formato de resposta
6. Rodar: `cd backend && pytest tests/ -v`
7. Commit seguindo Conventional Commits

## Criterios de aceite
- [x] Todos os endpoints de listagem retornam `{ items, total, page, page_size, pages }`
- [x] Parametros `page` e `page_size` funcionam corretamente
- [x] Testes atualizados e passando
- [x] Endpoint legado `/api/v1/estoque` NAO foi alterado (manter retrocompatibilidade)

## Notas
- **NAO alterar** o endpoint legado `GET /api/v1/estoque` - ele sera depreciado
- Parametros antigos `skip`/`limit` devem ser substituidos por `page`/`page_size`
- Usar `page` 1-indexed (mais intuitivo que 0-indexed)
- Consultar `AGENTS.md` para padroes do projeto
