---
task_id: TASK-005
title: "Otimizar query N+1 no endpoint de listagem de estoque"
priority: media
scope: backend/app/api/v1/estoque_v2.py
branch: perf/estoque-n1-query
commit_message: "perf(estoque): elimina N+1 na listagem com query agregada"
estimated_effort: 30 minutos
status: concluida
---

# TASK-005: Otimizar query N+1 no endpoint de listagem de estoque

## Contexto
O endpoint `GET /api/v2/estoque/` usa `selectinload(Produto.transacoes)` para carregar
TODAS as transacoes de todos os produtos na memoria, e depois calcula o estoque no Python
via `produto.estoque_atual` (que faz `sum(t.quantidade for t in self.transacoes)`).

**Problema:** Com 100 produtos e 10.000 transacoes, isso carrega 10.000 linhas na memoria
para calcular 100 somas. O correto e fazer isso no banco de dados com `SUM()` + `GROUP BY`.

## Arquivo afetado
- `backend/app/api/v1/estoque_v2.py` - funcao `listar_estoque_completo` (linhas 86-136)

## Codigo atual (PROBLEMA - N+1 com selectinload)
```python
@router.get("/", response_model=List[EstoqueAtual])
def listar_estoque_completo(
    apenas_ativos: bool = True,
    apenas_baixo: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    sub_ultima_data = (
        db.query(
            TransacaoEstoque.produto_id.label("produto_id"),
            func.max(TransacaoEstoque.data_transacao).label("ultima_data"),
        )
        .group_by(TransacaoEstoque.produto_id)
        .subquery()
    )

    query = (
        db.query(Produto, sub_ultima_data.c.ultima_data)
        .outerjoin(sub_ultima_data, sub_ultima_data.c.produto_id == Produto.id)
        .options(selectinload(Produto.transacoes))  #  PROBLEMA: carrega TUDO
    )

    if apenas_ativos:
        query = query.filter(Produto.ativo.is_(True))

    rows = query.all()

    resultado: List[EstoqueAtual] = []
    for produto, ultima_data in rows:
        quantidade_atual = produto.estoque_atual  #  Calcula em Python
        estoque = EstoqueAtual(
            produto_id=produto.id,
            nome_produto=produto.nome,
            quantidade_atual=quantidade_atual,
            estoque_minimo=produto.estoque_minimo,
            estoque_baixo=produto.estoque_baixo,
            ultima_movimentacao=ultima_data,
        )

        if apenas_baixo and not estoque.estoque_baixo:
            continue

        resultado.append(estoque)

    return resultado
```

## Codigo correto (SUBSTITUIR - query agregada no banco)
```python
@router.get("/", response_model=List[EstoqueAtual])
def listar_estoque_completo(
    apenas_ativos: bool = True,
    apenas_baixo: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista o estoque de todos os produtos.

    - **apenas_ativos**: Se True, lista apenas produtos ativos
    - **apenas_baixo**: Se True, lista apenas produtos com estoque baixo
    """
    # Subquery: calcula SUM e MAX no banco de dados (evita N+1)
    sub_estoque = (
        db.query(
            TransacaoEstoque.produto_id.label("produto_id"),
            func.coalesce(func.sum(TransacaoEstoque.quantidade), 0).label("quantidade_atual"),
            func.max(TransacaoEstoque.data_transacao).label("ultima_data"),
        )
        .group_by(TransacaoEstoque.produto_id)
        .subquery()
    )

    # Query principal: JOIN com subquery agregada (sem selectinload!)
    query = (
        db.query(
            Produto.id,
            Produto.nome,
            Produto.estoque_minimo,
            func.coalesce(sub_estoque.c.quantidade_atual, 0).label("quantidade_atual"),
            sub_estoque.c.ultima_data,
        )
        .outerjoin(sub_estoque, sub_estoque.c.produto_id == Produto.id)
    )

    if apenas_ativos:
        query = query.filter(Produto.ativo.is_(True))

    rows = query.all()

    resultado: List[EstoqueAtual] = []
    for row in rows:
        quantidade_atual = row.quantidade_atual
        estoque_baixo = quantidade_atual <= row.estoque_minimo

        if apenas_baixo and not estoque_baixo:
            continue

        resultado.append(
            EstoqueAtual(
                produto_id=row.id,
                nome_produto=row.nome,
                quantidade_atual=quantidade_atual,
                estoque_minimo=row.estoque_minimo,
                estoque_baixo=estoque_baixo,
                ultima_movimentacao=row.ultima_data,
            )
        )

    return resultado
```

## Impacto esperado

| Metrica | Antes | Depois |
|---------|-------|--------|
| Queries SQL | 1 (produtos) + 1 (selectin transacoes) | 1 (tudo agregado) |
| Dados carregados | Todas as transacoes (~10k rows) | Apenas resultados agregados (~100 rows) |
| Calculo da soma | Python (loop) | PostgreSQL (SUM) |
| Performance estimada | O(n * m) | O(n) |

## Passos
1. Criar branch `perf/estoque-n1-query`
2. No arquivo `backend/app/api/v1/estoque_v2.py`:
   - Substituir a funcao `listar_estoque_completo` pela versao otimizada
   - Remover `selectinload` do import se nao for mais usado em nenhum outro lugar
3. Rodar testes: `cd backend && pytest tests/ -v`
4. Verificar que o endpoint `GET /api/v2/estoque/` retorna os mesmos dados
5. Commit seguindo Conventional Commits

## Criterios de aceite
- [ ] Endpoint retorna os mesmos dados de antes (mesmo schema `EstoqueAtual`)
- [ ] Nenhum uso de `selectinload(Produto.transacoes)` no endpoint de listagem
- [ ] Testes existentes passam sem erros
- [ ] Filtro `apenas_ativos` e `apenas_baixo` funcionam corretamente

## Notas
- NAO alterar `obter_estoque_produto` (endpoint individual) - ele ja usa `func.sum` corretamente
- NAO alterar o model `Produto.estoque_atual` (property) - endpoints individuais podem usa-lo
- O `selectinload` pode ser mantido no import se outros endpoints o usarem
- Consultar `AGENTS.md` para padroes do projeto

## Atualizacao de status
-  Endpoint de listagem com abordagem agregada em banco (`SUM`/`GROUP BY` + `JOIN`)
-  Benchmark detalhado permanece no escopo da `TASK-010`
