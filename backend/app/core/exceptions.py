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


class QuantidadeInvalidaParaUnidadeError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="quantidade_invalida_para_unidade",
            message="Quantidade inválida para a unidade de medida do produto",
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


class ContaNaoEncontradaError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="conta_nao_encontrada",
            message="Conta não encontrada",
            status_code=404,
            details=details,
        )


class ContaJaBaixadaError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="conta_ja_baixada",
            message="Esta conta já foi baixada anteriormente",
            status_code=400,
            details=details,
        )


class ItemEstoqueNaoEncontradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="item_estoque_nao_encontrado",
            message="Item não encontrado",
            status_code=404,
            details=details,
        )


class FornecedorNaoEncontradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="fornecedor_nao_encontrado",
            message="Fornecedor não encontrado",
            status_code=404,
            details=details,
        )


class CnpjJaCadastradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="cnpj_ja_cadastrado",
            message="CNPJ já cadastrado",
            status_code=400,
            details=details,
        )


class FornecedorJaInativoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="fornecedor_ja_inativo",
            message="Fornecedor já está inativo",
            status_code=400,
            details=details,
        )


class FornecedorJaAtivoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="fornecedor_ja_ativo",
            message="Fornecedor já está ativo",
            status_code=400,
            details=details,
        )


class ClienteNaoIdentificadoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="cliente_nao_identificado",
            message="deve informar cliente_id ou cliente_nome",
            status_code=422,
            details=details,
        )


class OrcamentoNaoEncontradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="orcamento_nao_encontrado",
            message="Orçamento não encontrado",
            status_code=404,
            details=details,
        )


class OrcamentoNaoAbertoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="orcamento_nao_aberto",
            message="Apenas orçamentos abertos podem ser atualizados",
            status_code=400,
            details=details,
        )


class OrcamentoNaoCancelavelError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="orcamento_nao_cancelavel",
            message="Apenas orçamentos abertos ou aprovados podem ser convertidos",
            status_code=400,
            details=details,
        )


class SemItensElegiveisError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="sem_itens_elegiveis",
            message="Nenhum item elegível para venda",
            status_code=400,
            details=details,
        )


class CaixaNaoEncontradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="caixa_nao_encontrado",
            message="Caixa não encontrado",
            status_code=404,
            details=details,
        )


class CaixaJaAbertoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="caixa_ja_aberto",
            message="Já existe um caixa aberto para hoje",
            status_code=400,
            details=details,
        )


class CaixaNaoAbertoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="caixa_nao_aberto",
            message="Não há caixa aberto. Abra o caixa antes de registrar vendas",
            status_code=400,
            details=details,
        )


class CaixaJaFechadoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="caixa_ja_fechado",
            message="Este caixa já foi fechado",
            status_code=400,
            details=details,
        )


class DescontoExcedidoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="desconto_excedido",
            message="Desconto excede o máximo permitido pela política do produto",
            status_code=400,
            details=details,
        )
