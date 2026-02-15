---
task_id: TASK-001
title: "Corrigir uso depreciado de datetime.utcnow()"
priority: 🟡 média
scope: backend/ (3 arquivos, 5 ocorrências)
branch: fix/datetime-utcnow
commit_message: "fix(backend): substitui datetime.utcnow() por datetime.now(timezone.utc)"
estimated_effort: 10 minutos
status: concluída
---

# TASK-001: Corrigir `datetime.utcnow()` depreciado

## Contexto
`datetime.utcnow()` está **depreciado desde Python 3.12** (DeprecationWarning).
O método correto é `datetime.now(timezone.utc)`, que retorna um datetime **timezone-aware**.

## Arquivos afetados (5 ocorrências em 3 arquivos)

| Arquivo | Linha | Uso |
|---------|-------|-----|
| `backend/app/models/transacao_estoque.py` | 28 | `default=datetime.utcnow` |
| `backend/app/api/v1/ocr.py` | 28 | `now = datetime.utcnow()` |
| `backend/app/api/v1/ocr.py` | 42 | `datetime.utcnow() + timedelta(...)` |
| `backend/app/api/v1/ocr.py` | 147 | `datetime.utcnow().isoformat()` |
| `backend/tests/test_recommendations_impl.py` | 28 | `datetime.utcnow() - timedelta(...)` |

## Correções

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
> Verificar se `timezone` já está importado neste arquivo; se não, adicionar ao import.

## Passos
1. Criar branch `fix/datetime-utcnow`
2. Aplicar as 5 correções nos 3 arquivos listados acima
3. Verificar que não restam usos: `grep -r "utcnow" backend/`
4. Rodar testes: `cd backend && pytest tests/ -v`
5. Commit seguindo Conventional Commits

## Critérios de aceite
- [ ] `grep -r "utcnow" backend/` retorna zero resultados
- [ ] Testes passam sem erros
- [ ] Nenhum DeprecationWarning relacionado a datetime

## Referências
- [Python 3.12 changelog](https://docs.python.org/3.12/whatsnew/3.12.html)
- `AGENTS.md` — padrões do projeto

## Atualização de status
- ✅ Implementação presente no código atual (`datetime.now(timezone.utc)` nos pontos mapeados)
- ✅ Busca por `utcnow` no diretório `backend/` sem ocorrências
