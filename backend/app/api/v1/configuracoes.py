from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_async_db
from ...core.security import get_current_active_user_async
from ...models.user import User
from ...schemas.configuracao_loja import ConfiguracaoLojaRead, ConfiguracaoLojaUpdate
from ...services.configuracao_loja_service import obter_configuracao_loja_async

router = APIRouter(tags=["Configuracoes"])


@router.get("/loja", response_model=ConfiguracaoLojaRead)
async def buscar_configuracao_loja(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    _ = current_user
    return await obter_configuracao_loja_async(db)


@router.put("/loja", response_model=ConfiguracaoLojaRead)
async def atualizar_configuracao_loja(
    payload: ConfiguracaoLojaUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    _ = current_user
    configuracao = await obter_configuracao_loja_async(db)
    for campo, valor in payload.model_dump().items():
        setattr(configuracao, campo, valor)

    db.add(configuracao)
    await db.commit()
    await db.refresh(configuracao)
    return configuracao
