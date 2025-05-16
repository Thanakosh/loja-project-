from sqlalchemy import Column, Integer, String, Float, DateTime
from ..core.database import Base
from datetime import datetime

class Orcamento(Base):
    __tablename__ = "orcamentos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cliente = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    valor_total = Column(Float, nullable=False)
    data_criacao = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Orcamento(id={self.id}, cliente='{self.cliente}', valor_total={self.valor_total})>"