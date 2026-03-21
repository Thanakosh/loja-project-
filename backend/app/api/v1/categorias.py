from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_async_db
from ...core.limiter import limiter
from ...core.pagination import paginate_async
from ...core.security import get_current_active_user_async
from ...models.categoria import Categoria
from ...models.user import User
from ...schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaTreeNode, CategoriaUpdate
from ...schemas.pagination import PaginatedResponse

router = APIRouter(tags=["Categorias"])


def _build_tree(categorias: list[Categoria]) -> list[CategoriaTreeNode]:
    nodes = {
        categoria.id: CategoriaTreeNode(
            id=categoria.id,
            nome=categoria.nome,
            parent_id=categoria.parent_id,
            ativo=categoria.ativo,
            children=[],
        )
        for categoria in categorias
    }

    roots: list[CategoriaTreeNode] = []
    for categoria in categorias:
        node = nodes[categoria.id]
        if categoria.parent_id and categoria.parent_id in nodes:
            nodes[categoria.parent_id].children.append(node)
        else:
            roots.append(node)

    return roots


@router.post("/", response_model=CategoriaRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def criar_categoria(
    request: Request,
    response: Response,
    categoria: CategoriaCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    if categoria.parent_id:
        parent = await db.get(Categoria, categoria.parent_id)
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria pai nao encontrada")

    db_categoria = Categoria(**categoria.model_dump())
    db.add(db_categoria)
    await db.commit()
    await db.refresh(db_categoria)
    return db_categoria


@router.get("/", response_model=PaginatedResponse[CategoriaRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_categorias(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    incluir_inativas: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    query = select(Categoria)
    if not incluir_inativas:
        query = query.where(Categoria.ativo.is_(True))
    query = query.order_by(Categoria.nome.asc())
    return await paginate_async(db, query, page=page, page_size=page_size)


@router.get("/arvore", response_model=list[CategoriaTreeNode])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_categorias_arvore(
    request: Request,
    response: Response,
    incluir_inativas: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    query = select(Categoria)
    if not incluir_inativas:
        query = query.where(Categoria.ativo.is_(True))
    categorias = (await db.execute(query.order_by(Categoria.nome.asc()))).scalars().all()
    return _build_tree(categorias)


@router.get("/{categoria_id}", response_model=CategoriaRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def buscar_categoria(
    request: Request,
    response: Response,
    categoria_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria nao encontrada")
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def atualizar_categoria(
    request: Request,
    response: Response,
    categoria_id: int,
    payload: CategoriaUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria nao encontrada")

    data = payload.model_dump(exclude_unset=True)
    if "parent_id" in data:
        if data["parent_id"] == categoria_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria nao pode ser pai dela mesma")
        if data["parent_id"] is not None:
            parent = await db.get(Categoria, data["parent_id"])
            if not parent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria pai nao encontrada")

    for key, value in data.items():
        setattr(categoria, key, value)

    await db.commit()
    await db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def deletar_categoria(
    request: Request,
    response: Response,
    categoria_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria nao encontrada")

    categoria.ativo = False
    await db.commit()
    return {"ok": True, "message": "Categoria desativada com sucesso"}
