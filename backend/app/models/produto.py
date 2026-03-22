from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from ..core.database import Base


UNIDADES_FRACIONAVEIS = {"MT", "KG", "LT", "M2", "M3"}

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
    codigo_barras = Column(String(32), unique=True, nullable=True, index=True)
    unidade = Column(String)
    unidade_medida = Column(String(10), nullable=False, default="UN", server_default="UN")
    data_emissao = Column(Date)
    numero_nota = Column(String)
    cnpj_fornecedor = Column(String)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categoria.id"), nullable=True, index=True)
    
    # Precificação avançada
    preco_custo = Column(Float, nullable=True)
    preco_varejo = Column(Float, nullable=True)
    preco_atacado = Column(Float, nullable=True)
    qtd_minima_atacado = Column(Float, nullable=True)

    # Campos adicionais
    ativo = Column(Boolean, default=True, nullable=False)  # Soft delete
    estoque_minimo = Column(Integer, default=0)  # Alerta de estoque baixo

    # Embedding vetorial da descrição (JSON array de floats) para detecção de duplicatas
    embedding = Column(Text, nullable=True)
    
    # Relacionamentos
    transacoes = relationship(
        "TransacaoEstoque",
        back_populates="produto",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    fornecedor_rel = relationship("Fornecedor", back_populates="produtos")
    categoria = relationship("Categoria", back_populates="produtos")
    politicas_desconto = relationship("PoliticaDescontoProduto", back_populates="produto", cascade="all, delete-orphan")
    
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
        return f"<Produto(id={self.id}, nome='{self.nome}')>"

    @property
    def permite_fracionado(self) -> bool:
        unidade = (self.unidade_medida or "UN").upper()
        return unidade in UNIDADES_FRACIONAVEIS
