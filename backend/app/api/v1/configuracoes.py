from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.user import User
from ...schemas.configuracao_loja import ConfiguracaoLojaRead, ConfiguracaoLojaUpdate
from ...services.configuracao_loja_service import obter_configuracao_loja

router = APIRouter(tags=["Configuracoes"])


@router.get("/loja", response_model=ConfiguracaoLojaRead)
def buscar_configuracao_loja(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _ = current_user
    return obter_configuracao_loja(db)


@router.put("/loja", response_model=ConfiguracaoLojaRead)
def atualizar_configuracao_loja(
    payload: ConfiguracaoLojaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _ = current_user
    configuracao = obter_configuracao_loja(db)
    for campo, valor in payload.model_dump().items():
        setattr(configuracao, campo, valor)

    db.add(configuracao)
    db.commit()
    db.refresh(configuracao)
    return configuracao
