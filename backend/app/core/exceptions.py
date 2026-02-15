from typing import Any


class BusinessException(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        details: Any | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ProdutoNaoEncontradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="produto_nao_encontrado",
            message="Produto não encontrado",
            status_code=404,
            details=details,
        )


class EstoqueInsuficienteError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="estoque_insuficiente",
            message="Estoque insuficiente",
            status_code=400,
            details=details,
        )
