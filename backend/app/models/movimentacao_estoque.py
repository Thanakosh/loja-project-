from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class MovimentacaoEstoque(Base):
    """Movimentação de estoque detalhada importada de MOVPROD2.DBF."""
    __tablename__ = "movimentacao_estoque"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False, index=True)
    hora = Column(String(5))
    operador = Column(String(10))
    produto_id = Column(Integer, ForeignKey("produto.id"), index=True)
    codigo_legado = Column(Integer, index=True)
    nome_produto = Column(String(50))
    unidade = Column(String(2))
    saldo_anterior = Column(Float, default=0)
    entrada = Column(Float, default=0)
    saida = Column(Float, default=0)
    saldo_final = Column(Float, default=0)
    documento = Column(Integer)
    historico = Column(String(50))

    # Relationships
    produto = relationship("Produto")

    def __repr__(self):
        return f"<MovimentacaoEstoque(id={self.id}, data={self.data}, produto='{self.nome_produto}')>"
