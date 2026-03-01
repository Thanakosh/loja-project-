"""
Módulo LLM — Desativado nesta versão.

Integração com Ollama (modelos locais) e Open Interpreter foi removida.
Análise de notas fiscais via LLM está planejada para uma versão futura,
quando será reimplementada com uma arquitetura mais robusta (fila assíncrona
com persistência de estado).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ...core.config import settings
from ...core.limiter import limiter
from ...core.security import get_current_active_user
from ...models.user import User

router = APIRouter(tags=["LLM"])


@router.post("/ollama", summary="[DESATIVADO] Processamento por Ollama")
@limiter.limit(settings.RATE_LIMIT_LLM)
async def ollama_disabled(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
):
    raise HTTPException(
        status_code=422,
        detail=(
            "Integração com LLM/Ollama está desativada nesta versão. "
            "Use o fluxo de importação via XML da NFe."
        ),
    )
