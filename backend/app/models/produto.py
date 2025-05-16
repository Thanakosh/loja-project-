from sqlalchemy import Column, Integer, String, Float, Date
from ..core.database import Base

class Produto(Base):
    __tablename__ = "produto"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    fornecedor = Column(String, nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    preco_liquido = Column(Float, nullable=False)
    codigo_ncm = Column(String)
    unidade = Column(String)
    data_emissao = Column(Date)
    numero_nota = Column(String)
    cnpj_fornecedor = Column(String) 