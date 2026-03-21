"""Endpoints para leitura e atualização das configurações gerais da loja."""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.limiter import limiter
from ...core.security import get_current_active_user
from ...core.config import settings
from ...models.configuracao_loja import ConfiguracaoLoja
from ...models.user import User
from ...schemas.configuracao_loja import ConfiguracaoLojaRead, ConfiguracaoLojaUpdate

router = APIRouter(tags=["Configurações"])


def _get_or_create_config(db: Session) -> ConfiguracaoLoja:
    """Retorna a configuração atual ou cria uma com valores padrão."""
    config = db.query(ConfiguracaoLoja).order_by(ConfiguracaoLoja.id.desc()).first()
    if config is None:
        config = ConfiguracaoLoja()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("/loja", response_model=ConfiguracaoLojaRead, summary="Retorna a configuração atual da loja")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_configuracao_loja(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConfiguracaoLoja:
    _ = current_user
    return _get_or_create_config(db)


@router.put("/loja", response_model=ConfiguracaoLojaRead, summary="Atualiza a configuração da loja")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def update_configuracao_loja(
    request: Request,
    response: Response,
    payload: ConfiguracaoLojaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConfiguracaoLoja:
    _ = current_user
    config = _get_or_create_config(db)
    for field, value in payload.model_dump(exclude_unset=False).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config
