from fastapi import FastAPI
# Correção da importação: Use importação relativa
from .api.v1.estoque import router as estoque_router # Supondo que seu APIRouter em estoque.py se chame 'router'
from .api.v1.ocr import router as ocr_router

app = FastAPI()

# Inclua o router com um prefixo e tags (boas práticas)
app.include_router(
    estoque_router,
    prefix="/api/v1/estoque", # Define o prefixo da URL para todas as rotas de estoque
    tags=["Estoque"]          # Agrupa as rotas de estoque na documentação do Swagger
)

app.include_router(
    ocr_router,
    prefix="/api/v1/ocr",
    tags=["OCR"]
)

@app.get("/ping", tags=["Health Check"]) # Adicionar tag para organização
def ping():
    return "pong"