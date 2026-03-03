from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class CaixaDiario(Base):
    """Controle de abertura e fechamento de caixa diário."""

    __tablename__ = "caixa_diario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_abertura = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    data_fechamento = Column(DateTime, nullable=True)
    valor_abertura = Column(Float, nullable=False, default=0.0)
    valor_fechamento = Column(Float, nullable=True)
    status = Column(String(10), nullable=False, default="aberto", index=True)  # "aberto" | "fechado"
    observacao = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)

    # Relationships
    usuario = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<CaixaDiario(id={self.id}, status={self.status!r}, "
            f"abertura={self.data_abertura}, usuario_id={self.usuario_id})>"
        )
