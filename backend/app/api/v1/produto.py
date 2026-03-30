import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import String, cast, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_async_db
from ...core.exceptions import ProdutoJaAtivoError, ProdutoJaDesativadoError, ProdutoNaoEncontradoError
from ...core.limiter import limiter
from ...core.pagination import paginate_async
from ...core.security import get_current_active_user_async
from ...models.categoria import Categoria
from ...models.produto import Produto
from ...models.transacao_estoque import TipoTransacao, TransacaoEstoque
from ...models.user import User
from ...schemas.pagination import PaginatedResponse
from ...schemas.produto import ProdutoCreate, ProdutoRead
from ...schemas.produto_ncm import LoteNCMUpdate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Produto"])


async def _collect_descendant_ids(db: AsyncSession, categoria_id: int) -> set[int]:
    categorias = (await db.execute(select(Categoria.id, Categoria.parent_id))).all()
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
    return nome.strip().lower()


def _normalizar_codigo_barras(codigo_barras: str | None) -> str | None:
    if codigo_barras is None:
        return None
    normalized = codigo_barras.strip()
    return normalized or None


@router.post("/", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def criar_produto(
    request: Request,
    response: Response,
    produto: ProdutoCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    produto_dict = produto.model_dump()
    quantidade_inicial = produto_dict.pop("quantidade_inicial", 0) or 0
    produto_dict["unidade_medida"] = (produto_dict.get("unidade_medida") or "UN").upper()
    produto_dict["codigo_barras"] = _normalizar_codigo_barras(produto_dict.get("codigo_barras"))
    if not produto_dict.get("unidade"):
        produto_dict["unidade"] = produto_dict["unidade_medida"]

    nome_normalizado = _normalizar_nome(produto_dict["nome"])

    produto_existente = (
        await db.execute(
            select(Produto).where(
                func.lower(func.trim(Produto.nome)) == nome_normalizado,
                Produto.ativo.is_(True),
            )
        )
    ).scalars().first()

    if produto_existente:
        logger.info(
            "Produto com nome '%s' ja existe (id=%d). Somando estoque: +%s",
            produto_dict["nome"],
            produto_existente.id,
            quantidade_inicial,
        )
        novo_preco = produto_dict.get("preco_unitario")
        if novo_preco and novo_preco != produto_existente.preco_unitario:
            produto_existente.preco_unitario = novo_preco
            produto_existente.preco_liquido = produto_dict.get("preco_liquido", novo_preco)

        barcode_importado = produto_dict.get("codigo_barras")
        barcode_existente = _normalizar_codigo_barras(produto_existente.codigo_barras)
        barcode_status: str | None = None

        if barcode_importado:
            if not barcode_existente:
                produto_com_barcode = (
                    await db.execute(
                        select(Produto).where(
                            Produto.codigo_barras == barcode_importado,
                            Produto.id != produto_existente.id,
                        )
                    )
                ).scalars().first()
                if produto_com_barcode:
                    barcode_status = "conflito_outro_produto"
                else:
                    produto_existente.codigo_barras = barcode_importado
                    barcode_status = "preenchido"
            elif barcode_existente != barcode_importado:
                barcode_status = "conflito_preservado"

        if quantidade_inicial and quantidade_inicial > 0:
            db.add(
                TransacaoEstoque(
                    produto_id=produto_existente.id,
                    tipo=TipoTransacao.ENTRADA,
                    quantidade=quantidade_inicial,
                    motivo=f"Entrada via importacao de nota{' n° ' + produto_dict.get('numero_nota') if produto_dict.get('numero_nota') else ''}",
                    usuario_id=current_user.id,
                )
            )

        await db.commit()
        await db.refresh(produto_existente)
        response.headers["X-Produto-Acao"] = "estoque_somado"
        response.headers["X-Produto-Id-Existente"] = str(produto_existente.id)
        if barcode_status:
            response.headers["X-Produto-Barcode-Status"] = barcode_status
        return produto_existente

    categoria_id = produto_dict.get("categoria_id")
    if categoria_id is not None:
        categoria = (
            await db.execute(
                select(Categoria).where(Categoria.id == categoria_id, Categoria.ativo.is_(True))
            )
        ).scalars().first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    db_produto = Produto(**produto_dict)
    db.add(db_produto)
    await db.commit()
    await db.refresh(db_produto)

    if quantidade_inicial and quantidade_inicial > 0:
        db.add(
            TransacaoEstoque(
                produto_id=db_produto.id,
                tipo=TipoTransacao.ENTRADA,
                quantidade=quantidade_inicial,
                motivo="Estoque inicial via importacao de nota",
                usuario_id=current_user.id,
            )
        )
        await db.commit()
        await db.refresh(db_produto)

    response.headers["X-Produto-Acao"] = "criado"
    return db_produto


@router.get("/", response_model=PaginatedResponse[ProdutoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_produtos(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    incluir_inativos: bool = False,
    search: str = Query(None),
    barcode: str | None = Query(None),
    categoria_id: int | None = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    query = select(Produto)
    if not incluir_inativos:
        query = query.where(Produto.ativo.is_(True))
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Produto.nome.ilike(pattern),
                Produto.codigo_barras.ilike(pattern),
                cast(Produto.id, String).ilike(pattern),
            )
        )
    if barcode:
        query = query.where(Produto.codigo_barras == barcode.strip())
    if categoria_id is not None:
        categoria = (
            await db.execute(
                select(Categoria).where(Categoria.id == categoria_id, Categoria.ativo.is_(True))
            )
        ).scalars().first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria nao encontrada")
        categoria_ids = await _collect_descendant_ids(db, categoria_id)
        query = query.where(Produto.categoria_id.in_(categoria_ids))
    query = query.order_by(Produto.id.desc())
    return await paginate_async(db, query, page=page, page_size=page_size)


@router.get("/sem-ncm", response_model=PaginatedResponse[ProdutoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_produtos_sem_ncm(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str = Query(None),
    categoria_id: int | None = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    query = select(Produto).where(
        Produto.ativo.is_(True),
        or_(
            Produto.codigo_ncm.is_(None),
            Produto.codigo_ncm == "",
            func.length(Produto.codigo_ncm) < 8,
        ),
    )
    if search:
        query = query.where(Produto.nome.ilike(f"%{search}%"))
    if categoria_id is not None:
        categoria = (
            await db.execute(
                select(Categoria).where(Categoria.id == categoria_id, Categoria.ativo.is_(True))
            )
        ).scalars().first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria nao encontrada")
        categoria_ids = await _collect_descendant_ids(db, categoria_id)
        query = query.where(Produto.categoria_id.in_(categoria_ids))
    query = query.order_by(Produto.id.desc())
    return await paginate_async(db, query, page=page, page_size=page_size)


@router.get("/{produto_id}", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def buscar_produto(
    request: Request,
    response: Response,
    produto_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    produto = await db.get(Produto, produto_id)
    if not produto:
        raise ProdutoNaoEncontradoError()
    return produto


@router.put("/ncm/lote")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def atualizar_ncms_em_lote(
    request: Request,
    response: Response,
    payload: LoteNCMUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    ids_to_update = [item.id for item in payload.produtos]
    produtos = (
        await db.execute(select(Produto).where(Produto.id.in_(ids_to_update)))
    ).scalars().all()
    produtos_dict = {p.id: p for p in produtos}
    atualizados = 0
    for item in payload.produtos:
        if item.id in produtos_dict:
            produtos_dict[item.id].codigo_ncm = item.codigo_ncm
            atualizados += 1
    await db.commit()
    return {"ok": True, "message": f"{atualizados} produtos atualizados com sucesso"}


@router.put("/{produto_id}", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def atualizar_produto(
    request: Request,
    response: Response,
    produto_id: int,
    produto: ProdutoCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    db_produto = await db.get(Produto, produto_id)
    if not db_produto:
        raise ProdutoNaoEncontradoError()

    produto_dict = produto.model_dump()
    produto_dict.pop("quantidade_inicial", None)
    produto_dict["unidade_medida"] = (produto_dict.get("unidade_medida") or "UN").upper()
    if not produto_dict.get("unidade"):
        produto_dict["unidade"] = produto_dict["unidade_medida"]

    categoria_id = produto_dict.get("categoria_id")
    if categoria_id is not None:
        categoria = (
            await db.execute(
                select(Categoria).where(Categoria.id == categoria_id, Categoria.ativo.is_(True))
            )
        ).scalars().first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    for key, value in produto_dict.items():
        setattr(db_produto, key, value)
    await db.commit()
    await db.refresh(db_produto)
    return db_produto


@router.delete("/{produto_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def desativar_produto(
    request: Request,
    response: Response,
    produto_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    db_produto = await db.get(Produto, produto_id)
    if not db_produto:
        raise ProdutoNaoEncontradoError()
    if not db_produto.ativo:
        raise ProdutoJaDesativadoError()

    db_produto.ativo = False
    await db.commit()
    return {"ok": True, "message": "Produto desativado com sucesso"}


@router.delete("/{produto_id}/permanente")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def deletar_produto_permanente(
    request: Request,
    response: Response,
    produto_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    db_produto = await db.get(Produto, produto_id)
    if not db_produto:
        raise ProdutoNaoEncontradoError()

    nome = db_produto.nome
    estoque_atual = db_produto.estoque_atual
    qtd_transacoes = (
        await db.scalar(
            select(func.count()).select_from(TransacaoEstoque).where(
                TransacaoEstoque.produto_id == produto_id
            )
        )
    ) or 0

    await db.delete(db_produto)
    await db.commit()

    logger.warning(
        "Produto REMOVIDO PERMANENTEMENTE: id=%d nome='%s' estoque_era=%s transacoes_apagadas=%d usuario_id=%d",
        produto_id,
        nome,
        estoque_atual,
        qtd_transacoes,
        current_user.id,
    )

    return {
        "ok": True,
        "message": f"Produto '{nome}' removido permanentemente.",
        "transacoes_removidas": qtd_transacoes,
    }


@router.post("/{produto_id}/reativar", response_model=ProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def reativar_produto(
    request: Request,
    response: Response,
    produto_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    db_produto = await db.get(Produto, produto_id)
    if not db_produto:
        raise ProdutoNaoEncontradoError()
    if db_produto.ativo:
        raise ProdutoJaAtivoError()

    db_produto.ativo = True
    await db.commit()
    await db.refresh(db_produto)
    return db_produto
