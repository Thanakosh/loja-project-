from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from ..core.database import Base


class Venda(Base):
    """Cabeçalho de venda importado de VENDA.DBF."""
    __tablename__ = "venda"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_legado = Column(Integer, index=True, nullable=False)
    data = Column(Date, nullable=False, index=True)
    hora = Column(String(5))
    cliente_id = Column(Integer, ForeignKey("cliente.id"), index=True)
    caixa_id = Column(Integer, ForeignKey("caixa_diario.id"), nullable=True, index=True)
    vendedor = Column(String(10))
    total = Column(Float, default=0)
    desconto = Column(Float, default=0)
    forma_pagamento = Column(Integer)
    fatura = Column(String(10))
    situacao = Column(Integer, default=0)
    cancelada = Column(Boolean, default=False)
    cupom = Column(Integer, default=0)
    observacao = Column(String(120))
    autorizacao_terceiro_nome = Column(String(120), nullable=True)
    autorizacao_terceiro_documento = Column(String(30), nullable=True)
    autorizacao_terceiro_observacao = Column(String(255), nullable=True)
    entrega = Column(String(80))
    entrega_data = Column(Date)

    # Relationships
    cliente = relationship("Cliente", back_populates="vendas")
    itens = relationship("VendaItem", back_populates="venda", cascade="all, delete-orphan")
    pagamentos = relationship(
        "VendaPagamento",
        back_populates="venda",
        cascade="all, delete-orphan",
        order_by="VendaPagamento.ordem",
    )

    def __repr__(self):
        return f"<Venda(id={self.id}, numero_legado={self.numero_legado}, data={self.data}, total={self.total})>"


class VendaItem(Base):
    """Item de venda importado de VENDAIT.DBF."""
    __tablename__ = "venda_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venda_id = Column(Integer, ForeignKey("venda.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), index=True)
    codigo_legado = Column(Integer, index=True)
    nome_produto = Column(String(50))
    codigo_barras = Column(String(13))
    unidade = Column(String(2))
    quantidade = Column(Float, default=0)
    preco_unitario = Column(Float, default=0)
    preco_total = Column(Float, default=0)
    custo = Column(Float, default=0)
    desconto = Column(Float, default=0)
    desconto_motivo = Column(String(255))
    desconto_autorizado_por = Column(String(120))
    marca = Column(String(15))
    grupo = Column(Integer, default=0)

    # Relationships
    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto")

    def __repr__(self):
        return f"<VendaItem(id={self.id}, venda_id={self.venda_id}, nome='{self.nome_produto}', qtd={self.quantidade})>"


class VendaPagamento(Base):
    __tablename__ = "venda_pagamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venda_id = Column(Integer, ForeignKey("venda.id"), nullable=False, index=True)
    forma_pagamento = Column(Integer, nullable=False, index=True)
    valor = Column(Float, nullable=False, default=0)
    ordem = Column(Integer, nullable=False, default=1, index=True)
    valor_recebido = Column(Float, nullable=True)
    troco = Column(Float, nullable=False, default=0)

    venda = relationship("Venda", back_populates="pagamentos")

    def __repr__(self):
        return (
            f"<VendaPagamento(id={self.id}, venda_id={self.venda_id}, "
            f"forma_pagamento={self.forma_pagamento}, valor={self.valor})>"
        )
