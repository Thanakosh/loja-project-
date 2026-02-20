from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    razao_social = Column(String(120), nullable=False, index=True)
    nome_fantasia = Column(String(80))
    cnpj = Column(String(18), unique=True, index=True, nullable=False)
    telefone = Column(String(20))
    email = Column(String(120))
    endereco = Column(String(120))
    cidade = Column(String(60))
    uf = Column(String(2))
    cep = Column(String(10))
    prazo_pagamento_dias = Column(Integer, default=30)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=func.now(), nullable=False)
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())

    produtos = relationship("Produto", back_populates="fornecedor_rel", foreign_keys="Produto.fornecedor_id")
