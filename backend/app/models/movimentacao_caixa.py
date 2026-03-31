from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class MovimentacaoCaixa(Base):
    __tablename__ = "movimentacao_caixa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    caixa_id = Column(Integer, ForeignKey("caixa_diario.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False, index=True)
    valor = Column(Float, nullable=False)
    motivo = Column(String(120), nullable=False)
    observacao = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    caixa = relationship("CaixaDiario", back_populates="movimentacoes")
    usuario = relationship("User")

    @property
    def usuario_nome(self) -> str | None:
        user = self.usuario
        if not user:
            return None
        return user.username or user.full_name or user.email

    def __repr__(self) -> str:
        return (
            f"<MovimentacaoCaixa(id={self.id}, caixa_id={self.caixa_id}, "
            f"tipo={self.tipo!r}, valor={self.valor}, usuario_id={self.usuario_id})>"
        )
