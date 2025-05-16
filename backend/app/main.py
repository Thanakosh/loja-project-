from fastapi import FastAPI
from .api.v1.estoque import router as estoque_router
from .api.v1.orcamentos import router as orcamentos_router # <--- ADICIONE ESTA LINHA

app = FastAPI(title="Minha Loja API MVP") # Pode mudar o título se quiser

# Router de Estoque
app.include_router(
    estoque_router,
    prefix="/api/v1/estoque",
    tags=["Estoque"]
)

# Router de Orçamentos  <--- ADICIONE ESTE BLOCO INTEIRO
app.include_router(
    orcamentos_router,
    prefix="/api/v1/orcamentos",
    tags=["Orçamentos"]
)

@app.get("/ping", tags=["Health Check"])
def ping():
    return "pong"