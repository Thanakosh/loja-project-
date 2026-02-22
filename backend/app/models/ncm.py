from sqlalchemy import Column, String
from ..core.database import Base

class NCM(Base):
    __tablename__ = "ncm"
    
    codigo = Column(String(8), primary_key=True, index=True)
    descricao = Column(String, nullable=False)

    def __repr__(self):
        return f"<NCM(codigo='{self.codigo}', descricao='{self.descricao}')>"
