from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class PoliticaDescontoProduto(Base):
    """Faixas de desconto progressivo por produto/volume.

    Cada faixa define a quantidade mínima a partir da qual o vendedor
    pode conceder até ``desconto_maximo_percentual`` de desconto.
    As faixas são avaliadas da maior ``qtd_minima`` para a menor, de
    modo que a primeira faixa cuja ``qtd_minima`` seja <= à quantidade
    vendida determina o limite.

    Se o produto não possuir nenhuma política cadastrada, o vendedor
    tem liberdade total (comportamento legado).
    """

    __tablename__ = "politica_desconto_produto"

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False, index=True)
    qtd_minima = Column(Float, nullable=False, default=1)
    desconto_maximo_percentual = Column(Float, nullable=False)
    descricao = Column(String(120), nullable=True)

    produto = relationship("Produto", back_populates="politicas_desconto")

    def __repr__(self) -> str:
        return (
            f"<PoliticaDesconto produto_id={self.produto_id} "
            f"qtd>={self.qtd_minima} max={self.desconto_maximo_percentual}%>"
        )
