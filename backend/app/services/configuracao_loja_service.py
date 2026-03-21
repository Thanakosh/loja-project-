from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..models.configuracao_loja import ConfiguracaoLoja


def obter_configuracao_loja(db: Session) -> ConfiguracaoLoja:
    configuracao = (
        db.query(ConfiguracaoLoja)
        .order_by(ConfiguracaoLoja.updated_at.desc(), ConfiguracaoLoja.id.desc())
        .first()
    )
    if configuracao:
        return configuracao

    configuracao = ConfiguracaoLoja()
    db.add(configuracao)
    db.commit()
    db.refresh(configuracao)
    return configuracao


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
