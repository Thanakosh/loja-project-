from enum import Enum


class FormaPagamento(int, Enum):
    DINHEIRO = 1
    CARTAO_DEBITO = 2
    CARTAO_CREDITO = 3
    PIX = 4
    BOLETO = 5
    PRAZO = 6


class TipoMovimentacaoCaixa(str, Enum):
    SANGRIA = "sangria"
    SUPRIMENTO = "suprimento"
