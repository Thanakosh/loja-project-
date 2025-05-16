from sqlalchemy import Column, Integer, String
# Correção da importação:
# 'core' é um diretório irmão de 'models' (ambos dentro de 'app').
# Então, subimos um nível (de 'models' para 'app') com '..' e depois descemos para 'core'.
from ..core.database import Base

class Estoque(Base): # Este é o seu Modelo SQLAlchemy, que chamamos de EstoqueModel nas rotas
    __tablename__ = "estoque"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # Adicionado autoincrement=True
    nome = Column(String, index=True, nullable=False) # Adicionado index=True e nullable=False
    quantidade = Column(Integer, default=0, nullable=False) # Adicionado nullable=False

    def __repr__(self): # Opcional, mas útil para debugging
        return f"<Estoque(id={self.id}, nome='{self.nome}', quantidade={self.quantidade})>"