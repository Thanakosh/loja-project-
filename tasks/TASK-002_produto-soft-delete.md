---
task_id: TASK-002
title: "Ajustar DELETE de produto para usar soft delete"
priority: 🟡 média
scope: backend/app/api/v1/produto.py
branch: fix/produto-soft-delete
commit_message: "fix(produto): altera endpoint DELETE para usar soft delete (campo ativo)"
estimated_effort: 10 minutos
status: pendente
---

# TASK-002: Ajustar DELETE de produto para usar soft delete

## Contexto
O modelo `Produto` já possui o campo `ativo` (Boolean) preparado para soft delete,
mas o endpoint `DELETE /api/v1/produtos/{id}` faz **hard delete** (`db.delete()`),
o que apaga permanentemente o registro e todas as transações de estoque associadas
(por causa do `cascade="all, delete-orphan"`). Isso destrói o histórico de movimentações.

## Arquivo afetado
- `backend/app/api/v1/produto.py` (função `deletar_produto`, linhas ~87-99)

## Código atual (ERRADO)
```python
@router.delete("/{produto_id}")
def deletar_produto(
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deleta um produto (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(db_produto)
    db.commit()
    return {"ok": True}
```

## Código correto (SUBSTITUIR)
```python
@router.delete("/{produto_id}")
def deletar_produto(
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Desativa um produto via soft delete (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    if not db_produto.ativo:
        raise HTTPException(status_code=400, detail="Produto já está desativado")
    
    db_produto.ativo = False
    db.commit()
    return {"ok": True, "message": "Produto desativado com sucesso"}
```

## Alteração adicional: filtrar produtos inativos na listagem
No mesmo arquivo, atualizar `listar_produtos` para filtrar inativos por padrão:

```python
@router.get("/", response_model=List[ProdutoRead])
def listar_produtos(
    skip: int = 0, 
    limit: int = 100,
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os produtos (requer autenticação)"""
    query = db.query(Produto)
    if not incluir_inativos:
        query = query.filter(Produto.ativo == True)
    return query.offset(skip).limit(limit).all()
```

## Opcional: endpoint de reativação
```python
@router.post("/{produto_id}/reativar", response_model=ProdutoRead)
def reativar_produto(
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reativa um produto desativado (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if db_produto.ativo:
        raise HTTPException(status_code=400, detail="Produto já está ativo")
    db_produto.ativo = True
    db.commit()
    db.refresh(db_produto)
    return db_produto
```

## Passos
1. Criar branch `fix/produto-soft-delete`
2. No arquivo `backend/app/api/v1/produto.py`:
   - Alterar `deletar_produto` para fazer soft delete
   - Alterar `listar_produtos` para filtrar inativos por padrão
   - (Opcional) Adicionar endpoint `POST /{id}/reativar`
3. Rodar testes: `cd backend && pytest tests/ -v`
4. Commit seguindo Conventional Commits

## Critérios de aceite
- [ ] `DELETE /api/v1/produtos/{id}` marca `ativo=False` em vez de deletar
- [ ] `GET /api/v1/produtos` retorna apenas produtos ativos por padrão
- [ ] Parâmetro `incluir_inativos=true` mostra todos os produtos
- [ ] Histórico de transações é preservado após "exclusão"
- [ ] Testes passam sem erros
