from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from ..core.database import Base


class Cliente(Base):
    """Cliente normalizado a partir dos dados legados (VENDA.DBF + NF01.DBF)."""
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_legado = Column(Integer, unique=True, index=True, nullable=False)
    nome = Column(String(60), nullable=False, index=True)
    cpf_cnpj = Column(String(20), index=True)
    endereco = Column(String(80))
    cidade = Column(String(30))
    uf = Column(String(2))
    cep = Column(String(10))
    telefone = Column(String(20))
    email = Column(String(120))
    observacao = Column(String(255))
    historico_observacoes = Column(Text)
    inscricao_estadual = Column(String(20))
    ativo = Column(Boolean, default=True, nullable=False)

    # Relationships
    vendas = relationship("Venda", back_populates="cliente")
    contas_receber = relationship("ContaReceber", back_populates="cliente")
    notas_fiscais = relationship("NotaFiscal", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente(id={self.id}, codigo_legado={self.codigo_legado}, nome='{self.nome}')>"
