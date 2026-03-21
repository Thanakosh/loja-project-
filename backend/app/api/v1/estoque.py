from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_async_db
from ...core.exceptions import ItemEstoqueNaoEncontradoError
from ...core.security import get_current_active_user_async
from ...models.estoque import Estoque as EstoqueModel
from ...models.user import User
from ...schemas.estoque import EstoqueCreate, EstoqueRead

router = APIRouter(tags=["estoque"])


@router.post("/", response_model=EstoqueRead)
async def criar_estoque(
    item: EstoqueCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Cria um novo item no estoque (requer autenticaÃ§Ã£o)"""
    db_item = EstoqueModel(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.get("/", response_model=list[EstoqueRead])
async def listar_estoque(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Lista todos os itens do estoque (requer autenticaÃ§Ã£o)"""
    return (await db.execute(select(EstoqueModel))).scalars().all()


@router.get("/{item_id}", response_model=EstoqueRead)
async def obter_estoque(
    item_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """ObtÃ©m um item especÃ­fico do estoque (requer autenticaÃ§Ã£o)"""
    item = await db.get(EstoqueModel, item_id)
    if not item:
        raise ItemEstoqueNaoEncontradoError()
    return item


@router.put("/{item_id}", response_model=EstoqueRead)
async def atualizar_estoque(
    item_id: int,
    novo_item_data: EstoqueCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Atualiza um item do estoque (requer autenticaÃ§Ã£o)"""
    item = await db.get(EstoqueModel, item_id)
    if not item:
        raise ItemEstoqueNaoEncontradoError()

    item_data = novo_item_data.model_dump(exclude_unset=True)
    for key, value in item_data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}")
async def deletar_estoque(
    item_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Deleta um item do estoque (requer autenticaÃ§Ã£o)"""
    item = await db.get(EstoqueModel, item_id)
    if not item:
        raise ItemEstoqueNaoEncontradoError()
    await db.delete(item)
    await db.commit()
    return {"ok": True}
