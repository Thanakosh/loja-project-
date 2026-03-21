import logging
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
from sqlalchemy import or_, String, cast, func

logger = logging.getLogger(__name__)
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


def _normalizar_nome(nome: str) -> str:
    """Normaliza nome para comparação: lowercase e sem espaços extras."""
    return nome.strip().lower()


@router.post("/", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def criar_produto(
    request: Request,
    response: Response,
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cria um novo produto ou soma estoque se o nome já existir (requer autenticação)."""
    produto_dict = produto.model_dump()
    quantidade_inicial = produto_dict.pop("quantidade_inicial", 0) or 0
    produto_dict["unidade_medida"] = (produto_dict.get("unidade_medida") or "UN").upper()
    if not produto_dict.get("unidade"):
        produto_dict["unidade"] = produto_dict["unidade_medida"]

    nome_normalizado = _normalizar_nome(produto_dict["nome"])

    produto_existente = (
        db.query(Produto)
        .filter(
            func.lower(func.trim(Produto.nome)) == nome_normalizado,
            Produto.ativo.is_(True),
        )
        .first()
    )

    if produto_existente:
        logger.info(
            "Produto com nome '%s' já existe (id=%d). Somando estoque: +%s",
            produto_dict["nome"], produto_existente.id, quantidade_inicial,
        )
        novo_preco = produto_dict.get("preco_unitario")
        if novo_preco and novo_preco != produto_existente.preco_unitario:
            produto_existente.preco_unitario = novo_preco
            produto_existente.preco_liquido = produto_dict.get("preco_liquido", novo_preco)

        if quantidade_inicial and quantidade_inicial > 0:
            transacao = TransacaoEstoque(
                produto_id=produto_existente.id,
                tipo=TipoTransacao.ENTRADA,
                quantidade=quantidade_inicial,
                motivo=f"Entrada via importação de nota{' nº ' + produto_dict.get('numero_nota') if produto_dict.get('numero_nota') else ''}",
                usuario_id=current_user.id,
            )
            db.add(transacao)

        db.commit()
        db.refresh(produto_existente)
        response.headers["X-Produto-Acao"] = "estoque_somado"
        response.headers["X-Produto-Id-Existente"] = str(produto_existente.id)
        return produto_existente

    categoria_id = produto_dict.get("categoria_id")
    if categoria_id is not None:
        categoria = db.query(Categoria).filter(Categoria.id == categoria_id, Categoria.ativo.is_(True)).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")

    db_produto = Produto(**produto_dict)
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)

    if quantidade_inicial and quantidade_inicial > 0:
        transacao = TransacaoEstoque(
            produto_id=db_produto.id,
            tipo=TipoTransacao.ENTRADA,
            quantidade=quantidade_inicial,
            motivo="Estoque inicial via importação de nota",
            usuario_id=current_user.id,
        )
        db.add(transacao)
        db.commit()
        db.refresh(db_produto)

    response.headers["X-Produto-Acao"] = "criado"
    return db_produto


@router.get("/", response_model=PaginatedResponse[ProdutoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_produtos(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    incluir_inativos: bool = False,
    search: str = Query(None),
    barcode: str | None = Query(None),
    categoria_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Produto)
    if not incluir_inativos:
        query = query.filter(Produto.ativo.is_(True))
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Produto.nome.ilike(pattern),
                Produto.codigo_barras.ilike(pattern),
                cast(Produto.id, String).ilike(pattern)
            )
        )
    if barcode:
        query = query.filter(Produto.codigo_barras == barcode.strip())
    if categoria_id is not None:
        categoria = db.query(Categoria).filter(Categoria.id == categoria_id, Categoria.ativo.is_(True)).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        categoria_ids = _collect_descendant_ids(db, categoria_id)
        query = query.filter(Produto.categoria_id.in_(categoria_ids))
    query = query.order_by(Produto.id.desc())
    return paginate(query, page=page, page_size=page_size)


@router.get("/sem-ncm", response_model=PaginatedResponse[ProdutoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_produtos_sem_ncm(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str = Query(None),
    categoria_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
    ids_to_update = [item.id for item in payload.produtos]
    produtos = db.query(Produto).filter(Produto.id.in_(ids_to_update)).all()
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
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise ProdutoNaoEncontradoError()

    produto_dict = produto.model_dump()
    produto_dict.pop("quantidade_inicial", None)
    produto_dict["unidade_medida"] = (produto_dict.get("unidade_medida") or "UN").upper()
    if not produto_dict.get("unidade"):
        produto_dict["unidade"] = produto_dict["unidade_medida"]

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
def desativar_produto(
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


@router.delete("/{produto_id}/permanente")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def deletar_produto_permanente(
    request: Request,
    response: Response,
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove permanentemente um produto e todo o seu histórico de estoque. Irreversível."""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise ProdutoNaoEncontradoError()

    nome = db_produto.nome
    estoque_atual = db_produto.estoque_atual
    qtd_transacoes = db.query(TransacaoEstoque).filter(
        TransacaoEstoque.produto_id == produto_id
    ).count()

    # cascade="all, delete-orphan" no modelo apaga as transações automaticamente
    db.delete(db_produto)
    db.commit()

    logger.warning(
        "Produto REMOVIDO PERMANENTEMENTE: id=%d nome='%s' estoque_era=%s transacoes_apagadas=%d usuario_id=%d",
        produto_id, nome, estoque_atual, qtd_transacoes, current_user.id,
    )

    return {
        "ok": True,
        "message": f"Produto '{nome}' removido permanentemente.",
        "transacoes_removidas": qtd_transacoes,
    }


@router.post("/{produto_id}/reativar", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def reativar_produto(
    request: Request,
    response: Response,
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise ProdutoNaoEncontradoError()
    if db_produto.ativo:
        raise ProdutoJaAtivoError()

    db_produto.ativo = True
    db.commit()
    db.refresh(db_produto)
    return db_produto
