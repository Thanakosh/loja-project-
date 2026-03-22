from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from ..core.database import Base


class ConfiguracaoLoja(Base):
    __tablename__ = "configuracao_loja"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), nullable=True)
    razao_social = Column(String(160), nullable=True)
    nome_fantasia = Column(String(160), nullable=True)
    logradouro = Column(String(160), nullable=True)
    numero = Column(String(20), nullable=True)
    bairro = Column(String(100), nullable=True)
    municipio = Column(String(100), nullable=True)
    porte = Column(String(8), nullable=True)
    inscricao_estadual = Column(String(20), nullable=True)
    inscricao_municipal = Column(String(20), nullable=True)
    regime_tributario = Column(String(32), nullable=False, default="simples_nacional", server_default="simples_nacional")
    uf = Column(String(2), nullable=False, default="SP", server_default="SP")
    cep = Column(String(8), nullable=True)
    pais = Column(String(80), nullable=True)
    fone = Column(String(20), nullable=True)
    email = Column(String(160), nullable=True)
    cnae = Column(String(20), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), server_default=func.now())
