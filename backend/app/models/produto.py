from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from ..core.database import Base

class Produto(Base):
    __tablename__ = "produto"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    descricao = Column(String)
    fornecedor = Column(String, nullable=False)
    
    # Removido: quantidade (agora calculado a partir de transações)
    
    preco_unitario = Column(Float, nullable=False)
    preco_liquido = Column(Float, nullable=False)
    codigo_ncm = Column(String, index=True)
    unidade = Column(String)
    data_emissao = Column(Date)
    numero_nota = Column(String)
    cnpj_fornecedor = Column(String)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=True, index=True)
    
    # Campos adicionais
    ativo = Column(Boolean, default=True, nullable=False)  # Soft delete
    estoque_minimo = Column(Integer, default=0)  # Alerta de estoque baixo
    
    # Relacionamentos
    transacoes = relationship("TransacaoEstoque", back_populates="produto", cascade="all, delete-orphan")
    fornecedor_rel = relationship("Fornecedor", back_populates="produtos")
    
    @property
    def estoque_atual(self):
        """Calcula o estoque atual a partir das transações"""
        if not self.transacoes:
            return 0
        return sum(t.quantidade for t in self.transacoes)
    
    @property
    def estoque_baixo(self):
        """Verifica se o estoque está abaixo do mínimo"""
        return self.estoque_atual <= self.estoque_minimo
    
    def __repr__(self):
        return f"<Produto(id={self.id}, nome='{self.nome}', estoque={self.estoque_atual})>"
