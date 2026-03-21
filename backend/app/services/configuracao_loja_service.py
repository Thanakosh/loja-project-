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
