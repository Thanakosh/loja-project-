from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from ..core.database import Base
from datetime import date

class Orcamento(Base):
    __tablename__ = "orcamento"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    descricao = Column(String, nullable=False)
    valor_total = Column(Float, nullable=False)
    data_criacao = Column(Date, default=date.today, nullable=False)
    status = Column(String, default="aberto", nullable=False)
    cliente = Column(String, nullable=False) 