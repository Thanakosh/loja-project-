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


class VendaNaoEncontradaError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="venda_nao_encontrada",
            message="Venda não encontrada",
            status_code=404,
            details=details,
        )


class VendaJaCanceladaError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="venda_ja_cancelada",
            message="Venda já cancelada",
            status_code=400,
            details=details,
        )


class ClienteNaoEncontradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="cliente_nao_encontrado",
            message="Cliente não encontrado",
            status_code=404,
            details=details,
        )


class CodigoLegadoJaCadastradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="codigo_legado_ja_cadastrado",
            message="Código legado já cadastrado",
            status_code=400,
            details=details,
        )


class ProdutoJaDesativadoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="produto_ja_desativado",
            message="Produto já está desativado",
            status_code=400,
            details=details,
        )


class ProdutoJaAtivoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="produto_ja_ativo",
            message="Produto já está ativo",
            status_code=400,
            details=details,
        )
