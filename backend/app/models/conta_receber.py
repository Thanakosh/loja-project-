from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
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

    # Relationships
    cliente = relationship("Cliente", back_populates="contas_receber")

    @property
    def em_aberto(self):
        """Verifica se a conta ainda está em aberto."""
        return self.data_pagamento is None and self.valor_pago < self.valor

    def __repr__(self):
        return f"<ContaReceber(id={self.id}, doc={self.documento}, parcela={self.parcela}, valor={self.valor})>"
