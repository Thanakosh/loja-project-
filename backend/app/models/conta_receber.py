from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import query_expression, relationship

from ..core.database import Base


class ContaReceber(Base):
    """Conta a receber importada de CR.DBF."""

    __tablename__ = "conta_receber"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), index=True)
    documento = Column(Integer, index=True)
    parcela = Column(Integer)
    vendedor = Column(String(15))
    fatura = Column(String(10))
    data_emissao = Column(Date)
    data_vencimento = Column(Date, index=True)
    data_pagamento = Column(Date)
    valor = Column(Float, default=0)
    desconto = Column(Float, default=0)
    juros = Column(Float, default=0)
    valor_pago = Column(Float, default=0)
    historico = Column(String(40))
    cheque = Column(String(10))
    cobranca = Column(String(15))
    autorizacao_nome = Column(String(120))
    autorizacao_documento = Column(String(30))
    autorizacao_observacao = Column(String(255))
    total_parcelas = query_expression()

    cliente = relationship("Cliente", back_populates="contas_receber")

    @property
    def cliente_nome(self):
        return self.cliente.nome if self.cliente is not None else None

    @property
    def saldo_em_aberto(self):
        saldo = (
            (self.valor or 0)
            + (self.juros or 0)
            - (self.desconto or 0)
            - (self.valor_pago or 0)
        )
        return max(round(saldo, 2), 0.0)

    @property
    def em_aberto(self):
        return self.saldo_em_aberto > 0

    @property
    def situacao(self):
        if not self.em_aberto:
            return "quitada"
        if any(
            (
                (self.valor_pago or 0) > 0,
                (self.desconto or 0) > 0,
                (self.juros or 0) > 0,
                self.data_pagamento is not None,
            )
        ):
            return "parcial"
        return "aberta"

    def __repr__(self):
        return (
            f"<ContaReceber(id={self.id}, doc={self.documento}, "
            f"parcela={self.parcela}, valor={self.valor})>"
        )
