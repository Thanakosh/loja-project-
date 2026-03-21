---
task_id: TASK-001
title: "Corrigir uso depreciado de datetime.utcnow()"
priority: media
scope: backend/ (3 arquivos, 5 ocorrencias)
branch: fix/datetime-utcnow
commit_message: "fix(backend): substitui datetime.utcnow() por datetime.now(timezone.utc)"
estimated_effort: 10 minutos
status: concluida
---

# TASK-001: Corrigir `datetime.utcnow()` depreciado

## Contexto
`datetime.utcnow()` esta **depreciado desde Python 3.12** (DeprecationWarning).
O metodo correto e `datetime.now(timezone.utc)`, que retorna um datetime **timezone-aware**.

## Arquivos afetados (5 ocorrencias em 3 arquivos)

| Arquivo | Linha | Uso |
|---------|-------|-----|
| `backend/app/models/transacao_estoque.py` | 28 | `default=datetime.utcnow` |
| `backend/app/api/v1/ocr.py` | 28 | `now = datetime.utcnow()` |
| `backend/app/api/v1/ocr.py` | 42 | `datetime.utcnow() + timedelta(...)` |
| `backend/app/api/v1/ocr.py` | 147 | `datetime.utcnow().isoformat()` |
| `backend/tests/test_recommendations_impl.py` | 28 | `datetime.utcnow() - timedelta(...)` |

## Correcoes

### 1. `backend/app/models/transacao_estoque.py` (linha 28)
```python
# ANTES
from datetime import datetime
data_transacao = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

# DEPOIS
from datetime import datetime, timezone
data_transacao = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
```

### 2. `backend/app/api/v1/ocr.py` (linhas 28, 42, 147)
```python
# ANTES
from datetime import datetime, timedelta
now = datetime.utcnow()                                          # linha 28
return (datetime.utcnow() + timedelta(...)).isoformat()          # linha 42
"created_at": datetime.utcnow().isoformat(),                     # linha 147

# DEPOIS
from datetime import datetime, timedelta, timezone
now = datetime.now(timezone.utc)                                  # linha 28
return (datetime.now(timezone.utc) + timedelta(...)).isoformat()  # linha 42
"created_at": datetime.now(timezone.utc).isoformat(),             # linha 147
```

### 3. `backend/tests/test_recommendations_impl.py` (linha 28)
```python
# ANTES
"expires_at": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),

# DEPOIS
"expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
```
> Verificar se `timezone` ja esta importado neste arquivo; se nao, adicionar ao import.

## Passos
1. Criar branch `fix/datetime-utcnow`
2. Aplicar as 5 correcoes nos 3 arquivos listados acima
3. Verificar que nao restam usos: `grep -r "utcnow" backend/`
4. Rodar testes: `cd backend && pytest tests/ -v`
5. Commit seguindo Conventional Commits

## Criterios de aceite
- [ ] `grep -r "utcnow" backend/` retorna zero resultados
- [ ] Testes passam sem erros
- [ ] Nenhum DeprecationWarning relacionado a datetime

## Referencias
- [Python 3.12 changelog](https://docs.python.org/3.12/whatsnew/3.12.html)
- `AGENTS.md` - padroes do projeto

## Atualizacao de status
-  Implementacao presente no codigo atual (`datetime.now(timezone.utc)` nos pontos mapeados)
-  Busca por `utcnow` no diretorio `backend/` sem ocorrencias
