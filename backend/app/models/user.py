from sqlalchemy import Boolean, Column, Integer, JSON, String
from sqlalchemy.orm import relationship

from ..core.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    allowed_tabs = Column(JSON, default=list, nullable=False)
    
    # Relacionamentos
    transacoes_estoque = relationship("TransacaoEstoque", back_populates="usuario")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
