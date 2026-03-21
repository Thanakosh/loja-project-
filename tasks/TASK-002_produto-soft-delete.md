---
task_id: TASK-002
title: "Ajustar DELETE de produto para usar soft delete"
priority: media
scope: backend/app/api/v1/produto.py
branch: fix/produto-soft-delete
commit_message: "fix(produto): altera endpoint DELETE para usar soft delete (campo ativo)"
estimated_effort: 10 minutos
status: concluida
---

# TASK-002: Ajustar DELETE de produto para usar soft delete

## Contexto
O modelo `Produto` ja possui o campo `ativo` (Boolean) preparado para soft delete,
mas o endpoint `DELETE /api/v1/produtos/{id}` faz **hard delete** (`db.delete()`),
o que apaga permanentemente o registro e todas as transacoes de estoque associadas
(por causa do `cascade="all, delete-orphan"`). Isso destroi o historico de movimentacoes.

## Arquivo afetado
- `backend/app/api/v1/produto.py` (funcao `deletar_produto`, linhas ~87-99)

## Codigo atual (ERRADO)
```python
@router.delete("/{produto_id}")
def deletar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deleta um produto (requer autenticacao)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    db.delete(db_produto)
    db.commit()
    return {"ok": True}
```

## Codigo correto (SUBSTITUIR)
```python
@router.delete("/{produto_id}")
def deletar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Desativa um produto via soft delete (requer autenticacao)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    if not db_produto.ativo:
        raise HTTPException(status_code=400, detail="Produto ja esta desativado")

    db_produto.ativo = False
    db.commit()
    return {"ok": True, "message": "Produto desativado com sucesso"}
```

## Alteracao adicional: filtrar produtos inativos na listagem
No mesmo arquivo, atualizar `listar_produtos` para filtrar inativos por padrao:

```python
@router.get("/", response_model=List[ProdutoRead])
def listar_produtos(
    skip: int = 0,
    limit: int = 100,
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os produtos (requer autenticacao)"""
    query = db.query(Produto)
    if not incluir_inativos:
        query = query.filter(Produto.ativo == True)
    return query.offset(skip).limit(limit).all()
```

## Opcional: endpoint de reativacao
```python
@router.post("/{produto_id}/reativar", response_model=ProdutoRead)
def reativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reativa um produto desativado (requer autenticacao)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    if db_produto.ativo:
        raise HTTPException(status_code=400, detail="Produto ja esta ativo")
    db_produto.ativo = True
    db.commit()
    db.refresh(db_produto)
    return db_produto
```

## Passos
1. Criar branch `fix/produto-soft-delete`
2. No arquivo `backend/app/api/v1/produto.py`:
   - Alterar `deletar_produto` para fazer soft delete
   - Alterar `listar_produtos` para filtrar inativos por padrao
   - (Opcional) Adicionar endpoint `POST /{id}/reativar`
3. Rodar testes: `cd backend && pytest tests/ -v`
4. Commit seguindo Conventional Commits

## Criterios de aceite
- [ ] `DELETE /api/v1/produtos/{id}` marca `ativo=False` em vez de deletar
- [ ] `GET /api/v1/produtos` retorna apenas produtos ativos por padrao
- [ ] Parametro `incluir_inativos=true` mostra todos os produtos
- [ ] Historico de transacoes e preservado apos "exclusao"
- [ ] Testes passam sem erros
