from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from ..core.database import Base


class ConfiguracaoLoja(Base):
    __tablename__ = "configuracao_loja"

    id = Column(Integer, primary_key=True, autoincrement=True)
    regime_tributario = Column(String(32), nullable=False, default="simples_nacional", server_default="simples_nacional")
    uf = Column(String(2), nullable=False, default="SP", server_default="SP")
    margem_minima_percentual = Column(Float, nullable=False, default=0.05, server_default="0.05")
    aliquota_impostos_default = Column(Float, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), server_default=func.now())
