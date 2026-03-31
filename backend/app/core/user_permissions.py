from __future__ import annotations

from collections.abc import Iterable

from fastapi import Depends, HTTPException, status

from .security import get_current_active_user_async
from ..models.user import User

USER_TAB_IDS = (
    "caixa",
    "pdv",
    "vendas",
    "produtos",
    "estoque",
    "orcamentos",
    "fornecedores",
    "notas_fiscais",
    "importar_nota",
    "clientes",
    "contas_receber",
    "relatorios",
    "configuracoes",
)
USER_TAB_SET = frozenset(USER_TAB_IDS)


def normalize_allowed_tabs(allowed_tabs: Iterable[str] | None) -> list[str]:
    if not allowed_tabs:
        return []

    normalized: list[str] = []
    seen: set[str] = set()

    for tab_id in allowed_tabs:
        if not isinstance(tab_id, str):
            continue

        cleaned = tab_id.strip()
        if not cleaned or cleaned not in USER_TAB_SET or cleaned in seen:
            continue

        normalized.append(cleaned)
        seen.add(cleaned)

    return normalized


def has_tab_access(user: User, tab_id: str) -> bool:
    if user.is_superuser:
        return True

    return tab_id in normalize_allowed_tabs(getattr(user, "allowed_tabs", []))


async def require_superuser(
    current_user: User = Depends(get_current_active_user_async),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )

    return current_user
