"""Modelo de feedback fiscal para rastreabilidade e aprendizado contínuo (TASK-033)."""

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class FiscalFeedback(Base):
    __tablename__ = "fiscal_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Rastreabilidade da sugestão
    origem_sugestao = Column(
        Enum("validate_note", "suggest_price", "classify_ncm", "supplier_ranking", name="origem_sugestao_enum"),
        nullable=False,
        index=True,
    )
    versao_motor = Column(String(20), nullable=False)

    # Decisão do usuário
    decisao = Column(
        Enum("aceito", "rejeitado", "revisado", name="decisao_feedback_enum"),
        nullable=False,
        index=True,
    )

    # Referência opcional ao objeto auditado (ex: numero_nota, product_id)
    referencia_id = Column(String(80), nullable=True)
    observacao = Column(String(500), nullable=True)

    # Usuário que deu o feedback
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    # Relacionamentos
    user = relationship("User")

    def __repr__(self):
        return (
            f"<FiscalFeedback(id={self.id}, origem={self.origem_sugestao}, "
            f"decisao={self.decisao}, user_id={self.user_id})>"
        )
