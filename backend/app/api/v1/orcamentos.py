from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List

from ....core.database import get_db
# Schemas de orçamento que criamos anteriormente
from ....schemas.orcamento import OrcamentoCreate, OrcamentoItemRead, OrcamentoGeradoInfo
# Modelo de Estoque para buscar produtos
from ....models.estoque import Estoque as EstoqueModel
# Serviço de PDF que criamos
from ....services import pdf as pdf_service # Importando o módulo pdf de services

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
    produto_db = db.query(EstoqueModel).filter(EstoqueModel.id == item_orcamento.produto_id).first()
    if not produto_db:
        raise HTTPException(
            status_code=404,
            detail=f"Produto com ID {item_orcamento.produto_id} não encontrado no estoque."
        )

    # Verifica se há quantidade suficiente no estoque (opcional, mas recomendado)
    # if produto_db.quantidade &lt; item_orcamento.quantidade:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Quantidade insuficiente em estoque para o produto '{produto_db.nome}' (ID: {produto_db.id}). Pedido: {item_orcamento.quantidade}, Disponível: {produto_db.quantidade}"
    #     )

    subtotal_item = produto_db.preco * item_orcamento.quantidade
    valor_total_orcamento += subtotal_item

    item_data_para_pdf = OrcamentoItemRead(
        id=produto_db.id, # Usando o ID do produto como referência, poderia ser um ID de item_orcamento se fosse salvo no DB
        produto_id=produto_db.id, # Mantendo o produto_id para consistência com o schema
        quantidade=item_orcamento.quantidade,
        nome_produto=produto_db.nome,
        preco_unitario=produto_db.preco,
        subtotal=subtotal_item
    )
    itens_processados.append(item_data_para_pdf)

# Aqui você poderia salvar o orçamento no banco de dados se quisesse
# Por exemplo:
# db_orcamento = OrcamentoModel(cliente_nome=orcamento_in.cliente_nome, ..., valor_total=valor_total_orcamento)
# db.add(db_orcamento)
# db.commit()
# db.refresh(db_orcamento)
# orcamento_id_salvo = db_orcamento.id
# Para este MVP, vamos pular o salvamento do orçamento no DB e focar na geração do PDF.
orcamento_id_salvo = None # Simula que não foi salvo para passar ao PDF.

# Dados do orçamento para o PDF (excluindo a lista de itens que já está em itens_processados)
orcamento_data_para_pdf = orcamento_in.dict(exclude={"itens"})

try:
    caminho_pdf = pdf_service.gerar_pdf_orcamento(
        orcamento_data=orcamento_data_para_pdf,
        itens_processados=[item.model_dump() for item in itens_processados], # Pydantic v2 ou item.dict() para v1
        valor_total_orcamento=valor_total_orcamento,
        orcamento_id_ref=orcamento_id_salvo
    )
    nome_arquivo = caminho_pdf.split('/')[-1] if caminho_pdf else "erro.pdf"

return 
    OrcamentoGeradoInfo(
        mensagem="Orçamento em PDF gerado com sucesso!",
        caminho_pdf=caminho_pdf,  # Em um cenário real, você pode não querer expor o caminho do servidor
        nome_arquivo_pdf=nome_arquivo
    )
    
except Exception as e:
    # Logar o erro em um sistema de logging real
    print(f"Erro ao gerar PDF: {e}")
    raise HTTPException(status_code=500, detail=f"Erro interno ao gerar o PDF do orçamento: {str(e)}") # <--- CORRIGIDOfrom .api.v1.estoque import router as estoque_router
from .api.v1.orcamentos import router as orcamentos_router # <--- NOVA IMPORTAÇÃO

app = FastAPI(title="Minha Loja API MVP")

# Router de Estoque
app.include_router(
    estoque_router,
    prefix="/api/v1/estoque",
    tags=["Estoque"]
)

# Router de Orçamentos  <--- NOVO BLOCO
app.include_router(
    orcamentos_router,
    prefix="/api/v1/orcamentos",
    tags=["Orçamentos"]
)

@app.get("/ping", tags=["Health Check"])
def ping():
    return "pong"