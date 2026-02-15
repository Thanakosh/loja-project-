from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings


def get_user_or_ip(request: Request) -> str:
    """
    Resolve a chave de rate limit por usuário autenticado ou por IP.

    Prioriza usuário autenticado quando presente no request.state.
    Em requisições anônimas, usa endereço IP remoto.
    """
    user = getattr(request.state, "current_user", None)

    if user and hasattr(user, "id"):
        return f"user:{user.id}"

    return get_remote_address(request)


limiter = Limiter(
    key_func=get_user_or_ip,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    headers_enabled=True,
)
