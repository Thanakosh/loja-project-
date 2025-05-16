from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List

from ....core.database import get_db
from ....schemas.orcamento import OrcamentoCreate, OrcamentoItemRead, OrcamentoGeradoInfo
from ....models.estoque import Estoque as EstoqueModel
from ....services import pdf as pdf_service

router = APIRouter()

@router.post("/", response_model=OrcamentoGeradoInfo, tags=["Orçamentos"])
async def criar_e_gerar_pdf_orcamento(
    orcamento_in: OrcamentoCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Cria um orçamento, processa os itens e gera um PDF.
    """
    itens_processados: List[OrcamentoItemRead] = []
    valor_total_orcamento = 0.0

    # Corrigido: iterar sobre os itens do orçamento
    for item_orcamento in orcamento_in.itens:
        produto_db = db.query(EstoqueModel).filter(EstoqueModel.id == item_orcamento.produto_id).first()
        if not produto_db:
            raise HTTPException(
                status_code=404,
                detail=f"Produto com ID {item_orcamento.produto_id} não encontrado no estoque."
            )

        # Verifica se há quantidade suficiente no estoque (descomente se quiser usar)
        # if produto_db.quantidade < item_orcamento.quantidade:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Quantidade insuficiente em estoque para o produto '{produto_db.nome}' (ID: {produto_db.id}). Pedido: {item_orcamento.quantidade}, Disponível: {produto_db.quantidade}"
        #     )

        subtotal_item = produto_db.preco * item_orcamento.quantidade
        valor_total_orcamento += subtotal_item

        item_data_para_pdf = OrcamentoItemRead(
            id=produto_db.id,
            produto_id=produto_db.id,
            quantidade=item_orcamento.quantidade,
            nome_produto=produto_db.nome,
            preco_unitario=produto_db.preco,
            subtotal=subtotal_item
        )
        itens_processados.append(item_data_para_pdf)

    # Simula que não foi salvo para passar ao PDF.
    orcamento_id_salvo = None

    # Dados do orçamento para o PDF (excluindo a lista de itens que já está em itens_processados)
    orcamento_data_para_pdf = orcamento_in.dict(exclude={"itens"})

    try:
        caminho_pdf = pdf_service.gerar_pdf_orcamento(
            orcamento_data=orcamento_data_para_pdf,
            itens_processados=[item.model_dump() for item in itens_processados],  # Para Pydantic v2
            valor_total_orcamento=valor_total_orcamento,
            orcamento_id_ref=orcamento_id_salvo
        )
        nome_arquivo = caminho_pdf.split('/')[-1] if caminho_pdf else "erro.pdf"

        return OrcamentoGeradoInfo(
            mensagem="Orçamento em PDF gerado com sucesso!",
            caminho_pdf=caminho_pdf,
            nome_arquivo_pdf=nome_arquivo
        )
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar o PDF do orçamento: {str(e)}")