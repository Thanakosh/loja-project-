from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class Categoria(Base):
    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("categoria.id", ondelete="SET NULL"), nullable=True, index=True)
    ativo = Column(Boolean, default=True, nullable=False)

    parent = relationship("Categoria", remote_side=[id], back_populates="children")
    children = relationship("Categoria", back_populates="parent")
    produtos = relationship("Produto", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria(id={self.id}, nome='{self.nome}', parent_id={self.parent_id})>"
