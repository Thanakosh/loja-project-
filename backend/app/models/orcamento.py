from enum import Enum

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class StatusOrcamento(str, Enum):
    ABERTO = "aberto"
    APROVADO = "aprovado"
    CANCELADO = "cancelado"
    CONVERTIDO = "convertido"


class Orcamento(Base):
    __tablename__ = "orcamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=True, index=True)
    cliente_nome = Column(String(120))
    status = Column(String(20), default=StatusOrcamento.ABERTO.value, nullable=False)
    desconto_geral = Column(Float, default=0.0)
    observacao = Column(String(255))
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_validade = Column(Date, nullable=True)
    venda_id = Column(Integer, ForeignKey("venda.id"), nullable=True)
    criado_por = Column(Integer, ForeignKey("user.id"), nullable=True)

    itens = relationship("OrcamentoItem", back_populates="orcamento", cascade="all, delete-orphan")
    cliente = relationship("Cliente", foreign_keys=[cliente_id])
    venda = relationship("Venda", foreign_keys=[venda_id])


class OrcamentoItem(Base):
    __tablename__ = "orcamento_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orcamento_id = Column(Integer, ForeignKey("orcamento.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=True)
    descricao = Column(String(120), nullable=False)
    quantidade = Column(Float, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    desconto = Column(Float, default=0.0)
    preco_total = Column(Float, nullable=False)

    orcamento = relationship("Orcamento", back_populates="itens")
    produto = relationship("Produto")
