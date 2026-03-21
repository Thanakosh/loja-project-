from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from ..core.database import Base


class ConfiguracaoLoja(Base):
    """Configurações gerais da loja (singleton — apenas 1 registro ativo)."""

    __tablename__ = "configuracao_loja"

    id = Column(Integer, primary_key=True, autoincrement=True)
    regime_tributario = Column(
        String(20),
        nullable=False,
        default="simples_nacional",
        comment="simples_nacional | regime_normal",
    )
    uf = Column(String(2), nullable=False, default="SP", comment="Sigla do estado (ex: SP, RJ, MG)")
    margem_minima_percentual = Column(
        Float,
        nullable=False,
        default=0.05,
        comment="Margem mínima para cálculo de preço mínimo (ex: 0.05 = 5%)",
    )
    aliquota_impostos_default = Column(
        Float,
        nullable=True,
        comment="Alíquota padrão de impostos (ex: 0.12 = 12%)",
    )
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    def __repr__(self) -> str:
        return (
            f"<ConfiguracaoLoja(id={self.id}, regime={self.regime_tributario!r}, "
            f"uf={self.uf!r}, margem={self.margem_minima_percentual})>"
        )
