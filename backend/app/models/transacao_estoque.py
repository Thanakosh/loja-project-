from datetime import UTC, datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class TipoTransacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    AJUSTE = "ajuste"
    DEVOLUCAO = "devolucao"


class TransacaoEstoque(Base):
    """
    Registra todas as movimentações de estoque.
    O estoque atual é calculado dinamicamente a partir das transações.
    """
    __tablename__ = "transacao_estoque"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False, index=True)
    tipo = Column(SQLEnum(TipoTransacao), nullable=False)
    quantidade = Column(Float, nullable=False)  # Positivo para entrada, negativo para saída
    motivo = Column(String, nullable=True)  # Ex: "Venda", "Compra", "Ajuste de inventário"
    usuario_id = Column(Integer, ForeignKey("user.id"), nullable=True)  # Quem fez a transação
    data_transacao = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
        index=True,
    )
    
    # Relacionamentos
    produto = relationship("Produto", back_populates="transacoes")
    usuario = relationship("User", back_populates="transacoes_estoque")
    
    def __repr__(self):
        return f"<TransacaoEstoque(id={self.id}, produto_id={self.produto_id}, tipo={self.tipo}, quantidade={self.quantidade})>"
