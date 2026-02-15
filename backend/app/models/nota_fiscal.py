from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class NotaFiscal(Base):
    """NF-e cabeçalho importada de NF01.DBF."""
    __tablename__ = "nota_fiscal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_legado = Column(Integer, index=True, nullable=False)
    chave_acesso = Column(String(44), index=True)
    serie = Column(String(3))
    data_emissao = Column(Date, index=True)
    hora_emissao = Column(String(8))
    data_saida = Column(Date)
    hora_saida = Column(String(8))
    situacao = Column(Integer, default=0)
    entrada_saida = Column(String(1))
    cfop = Column(String(5))
    cfop_descricao = Column(String(50))
    cliente_id = Column(Integer, ForeignKey("cliente.id"), index=True)
    protocolo = Column(String(15))
    data_protocolo = Column(String(20))
    protocolo_cancelamento = Column(String(20))
    data_cancelamento = Column(Date)
    valor_produtos = Column(Float, default=0)
    valor_total = Column(Float, default=0)
    valor_desconto = Column(Float, default=0)
    valor_frete = Column(Float, default=0)
    valor_icms = Column(Float, default=0)
    base_icms = Column(Float, default=0)
    base_substituicao = Column(Float, default=0)
    valor_substituicao = Column(Float, default=0)
    valor_ipi = Column(Float, default=0)
    valor_seguro = Column(Float, default=0)
    valor_outras = Column(Float, default=0)
    observacao = Column(String(80))

    # Relationships
    cliente = relationship("Cliente", back_populates="notas_fiscais")
    itens = relationship("NotaFiscalItem", back_populates="nota_fiscal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<NotaFiscal(id={self.id}, numero_legado={self.numero_legado}, chave='{self.chave_acesso}')>"


class NotaFiscalItem(Base):
    """Item de NF-e importado de NF02.DBF."""
    __tablename__ = "nota_fiscal_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_fiscal_id = Column(Integer, ForeignKey("nota_fiscal.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), index=True)
    codigo_legado = Column(Integer, index=True)
    nome_produto = Column(String(50))
    unidade = Column(String(2))
    quantidade = Column(Float, default=0)
    preco_unitario = Column(Float, default=0)
    preco_total = Column(Float, default=0)
    icms = Column(Float, default=0)
    ipi = Column(Float, default=0)
    cfop = Column(String(5))
    cst = Column(String(3))
    ncm = Column(String(8))
    codigo_barras = Column(String(13))
    pis = Column(Float, default=0)
    cofins = Column(Float, default=0)
    cest = Column(String(7))
    pedido = Column(String(10))

    # Relationships
    nota_fiscal = relationship("NotaFiscal", back_populates="itens")
    produto = relationship("Produto")

    def __repr__(self):
        return f"<NotaFiscalItem(id={self.id}, nf_id={self.nota_fiscal_id}, nome='{self.nome_produto}')>"
