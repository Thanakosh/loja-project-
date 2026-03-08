"""Modelo de feedback fiscal para rastreabilidade e aprendizado contínuo (TASK-033)."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class FiscalFeedback(Base):
    __tablename__ = "fiscal_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Rastreabilidade da sugestão
    origem_sugestao = Column(String(30), nullable=False, index=True)
    versao_motor = Column(String(20), nullable=False)

    # Decisão do usuário
    decisao = Column(String(20), nullable=False, index=True)

    # Valores financeiros opcionalmente auditáveis
    valor_original = Column(Numeric(12, 2), nullable=True)
    valor_final = Column(Numeric(12, 2), nullable=True)
    comentario = Column(String(500), nullable=True)

    # Referências opcionais
    nota_fiscal_id = Column(Integer, ForeignKey("nota_fiscal.id"), nullable=True, index=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=True, index=True)

    # Usuário que deu o feedback
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    # Relacionamentos
    user = relationship("User")
    nota_fiscal = relationship("NotaFiscal")
    produto = relationship("Produto")

    def __repr__(self):
        return (
            f"<FiscalFeedback(id={self.id}, origem={self.origem_sugestao}, "
            f"decisao={self.decisao}, user_id={self.user_id})>"
        )
