from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class CaixaDiario(Base):
    """Controle de abertura e fechamento de caixa diário."""

    __tablename__ = "caixa_diario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_abertura = Column(DateTime, nullable=False, default=datetime.now, index=True)
    data_fechamento = Column(DateTime, nullable=True)
    valor_abertura = Column(Float, nullable=False, default=0.0)
    valor_fechamento = Column(Float, nullable=True)
    status = Column(String(10), nullable=False, default="aberto", index=True)  # "aberto" | "fechado"
    observacao = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    usuario_fechamento_id = Column(Integer, ForeignKey("user.id"), nullable=True, index=True)

    # Relationships
    usuario_abertura = relationship("User", foreign_keys=[usuario_id])
    usuario_fechamento = relationship("User", foreign_keys=[usuario_fechamento_id])
    movimentacoes = relationship(
        "MovimentacaoCaixa",
        back_populates="caixa",
        cascade="all, delete-orphan",
        order_by="MovimentacaoCaixa.created_at.desc()",
    )

    @property
    def usuario_abertura_id(self) -> int:
        return self.usuario_id

    @property
    def usuario_abertura_nome(self) -> str | None:
        user = self.usuario_abertura
        if not user:
            return None
        return user.username or user.full_name or user.email

    @property
    def usuario_fechamento_nome(self) -> str | None:
        user = self.usuario_fechamento
        if not user:
            return None
        return user.username or user.full_name or user.email

    def __repr__(self) -> str:
        return (
            f"<CaixaDiario(id={self.id}, status={self.status!r}, "
            f"abertura={self.data_abertura}, usuario_id={self.usuario_id}, "
            f"usuario_fechamento_id={self.usuario_fechamento_id})>"
        )
