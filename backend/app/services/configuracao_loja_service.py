from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.configuracao_loja import ConfiguracaoLoja


async def obter_configuracao_loja_async(db: AsyncSession) -> ConfiguracaoLoja:
    result = await db.execute(
        select(ConfiguracaoLoja)
        .order_by(ConfiguracaoLoja.updated_at.desc(), ConfiguracaoLoja.id.desc())
    )
    configuracao = result.scalars().first()
    if configuracao:
        return configuracao

    configuracao = ConfiguracaoLoja()
    db.add(configuracao)
    await db.commit()
    await db.refresh(configuracao)
    return configuracao
