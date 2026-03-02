from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, UploadFile, File
from sqlalchemy.orm import Session
from ...core.config import settings
from ...core.database import get_db
from ...core.exceptions import ProdutoJaAtivoError, ProdutoJaDesativadoError, ProdutoNaoEncontradoError
from ...core.limiter import limiter
from ...core.pagination import paginate
from ...core.security import get_current_active_user
from ...models.categoria import Categoria
from ...models.produto import Produto
from ...models.user import User
from ...models.transacao_estoque import TransacaoEstoque, TipoTransacao
from ...schemas.pagination import PaginatedResponse
from ...schemas.produto import ProdutoCreate, ProdutoRead
from ...schemas.produto_ncm import LoteNCMUpdate
from sqlalchemy import or_

router = APIRouter(tags=["Produto"])


def _collect_descendant_ids(db: Session, categoria_id: int) -> set[int]:
    categorias = db.query(Categoria.id, Categoria.parent_id).all()
    children_map: dict[int | None, list[int]] = {}
    for item_id, parent_id in categorias:
        children_map.setdefault(parent_id, []).append(item_id)

    ids = {categoria_id}
    stack = [categoria_id]
    while stack:
        current = stack.pop()
        for child_id in children_map.get(current, []):
            if child_id not in ids:
                ids.add(child_id)
                stack.append(child_id)
    return ids

@router.post("/", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def criar_produto(
    request: Request,
    response: Response,
    produto: ProdutoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cria um novo produto (requer autenticação)"""
    # Extrair quantidade_inicial do schema antes de criar o modelo Produto
    produto_dict = produto.model_dump()
    quantidade_inicial = produto_dict.pop("quantidade_inicial", 0)
    
    categoria_id = produto_dict.get("categoria_id")
    if categoria_id is not None:
        categoria = db.query(Categoria).filter(Categoria.id == categoria_id, Categoria.ativo.is_(True)).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")

    db_produto = Produto(**produto_dict)
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    
    # Se houver quantidade inicial, criar uma transação de estoque
    if quantidade_inicial > 0:
        transacao = TransacaoEstoque(
            produto_id=db_produto.id,
            tipo=TipoTransacao.ENTRADA,
            quantidade=quantidade_inicial,
            motivo="Estoque inicial",
            usuario_id=current_user.id
        )
        db.add(transacao)
        db.commit()
        db.refresh(db_produto) # Atualizar para refletir estoque calculado
        
    return db_produto

@router.get("/", response_model=PaginatedResponse[ProdutoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_produtos(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=200, description="Itens por página"),
    incluir_inativos: bool = False,
    search: str = Query(None, description="Buscar por nome do produto"),
    categoria_id: int | None = Query(None, description="Filtrar por categoria e subcategorias"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os produtos com paginação (requer autenticação)"""
    query = db.query(Produto)
    if not incluir_inativos:
        query = query.filter(Produto.ativo.is_(True))
    if search:
        query = query.filter(Produto.nome.ilike(f"%{search}%"))
    if categoria_id is not None:
        categoria = db.query(Categoria).filter(Categoria.id == categoria_id, Categoria.ativo.is_(True)).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        categoria_ids = _collect_descendant_ids(db, categoria_id)
        query = query.filter(Produto.categoria_id.in_(categoria_ids))
    return paginate(query, page=page, page_size=page_size)

@router.get("/sem-ncm", response_model=PaginatedResponse[ProdutoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_produtos_sem_ncm(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=200, description="Itens por página"),
    search: str = Query(None, description="Buscar por nome do produto"),
    categoria_id: int | None = Query(None, description="Filtrar por categoria e subcategorias"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os produtos com NCM ausente ou inválido (requer autenticação)"""
    from sqlalchemy import func
    query = db.query(Produto).filter(
        Produto.ativo == True,
        or_(
            Produto.codigo_ncm == None,
            Produto.codigo_ncm == "",
            func.length(Produto.codigo_ncm) < 8
        )
    )
    if search:
        query = query.filter(Produto.nome.ilike(f"%{search}%"))
    if categoria_id is not None:
        categoria = db.query(Categoria).filter(Categoria.id == categoria_id, Categoria.ativo.is_(True)).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        categoria_ids = _collect_descendant_ids(db, categoria_id)
        query = query.filter(Produto.categoria_id.in_(categoria_ids))
    return paginate(query, page=page, page_size=page_size)

@router.get("/{produto_id}", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def buscar_produto(
    request: Request,
    response: Response,
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Busca um produto específico (requer autenticação)"""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise ProdutoNaoEncontradoError()
    return produto

@router.put("/ncm/lote")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def atualizar_ncms_em_lote(
    request: Request,
    response: Response,
    payload: LoteNCMUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza o NCM de vários produtos de uma só vez"""
    ids_to_update = [item.id for item in payload.produtos]
    produtos = db.query(Produto).filter(Produto.id.in_(ids_to_update)).all()
    
    # Criar dict para busca rápida
    produtos_dict = {p.id: p for p in produtos}
    
    atualizados = 0
    for item in payload.produtos:
        if item.id in produtos_dict:
            produtos_dict[item.id].codigo_ncm = item.codigo_ncm
            atualizados += 1
            
    db.commit()
    return {"ok": True, "message": f"{atualizados} produtos atualizados com sucesso"}

@router.put("/{produto_id}", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def atualizar_produto(
    request: Request,
    response: Response,
    produto_id: int, 
    produto: ProdutoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza um produto (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise ProdutoNaoEncontradoError()
    
    produto_dict = produto.model_dump()
    produto_dict.pop("quantidade_inicial", None) # Não atualizamos estoque por aqui
    
    categoria_id = produto_dict.get("categoria_id")
    if categoria_id is not None:
        categoria = db.query(Categoria).filter(Categoria.id == categoria_id, Categoria.ativo.is_(True)).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")

    for key, value in produto_dict.items():
        setattr(db_produto, key, value)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@router.delete("/{produto_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def deletar_produto(
    request: Request,
    response: Response,
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Desativa um produto via soft delete (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise ProdutoNaoEncontradoError()

    if not db_produto.ativo:
        raise ProdutoJaDesativadoError()

    db_produto.ativo = False
    db.commit()
    return {"ok": True, "message": "Produto desativado com sucesso"}


@router.post("/{produto_id}/reativar", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def reativar_produto(
    request: Request,
    response: Response,
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reativa um produto desativado (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise ProdutoNaoEncontradoError()
    if db_produto.ativo:
        raise ProdutoJaAtivoError()

    db_produto.ativo = True
    db.commit()
    db.refresh(db_produto)
    return db_produto
