from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.estoque import router as estoque_router
from app.api.v1.estoque_v2 import router as estoque_v2_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.users import router as users_router
from app.api.v1.llm import router as llm_router
from app.api.v1.orcamento import router as orcamento_router
from app.api.v1.produto import router as produto_router
from .core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para gerenciamento de loja com OCR e IA",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"]
)

app.include_router(
    estoque_router,
    prefix="/api/v1/estoque",
    tags=["Estoque (Legado)"]
)

app.include_router(
    estoque_v2_router,
    prefix="/api/v2/estoque",
    tags=["Estoque V2"]
)

app.include_router(
    produto_router,
    prefix="/api/v1/produtos",
    tags=["Produtos"]
)

app.include_router(
    ocr_router,
    prefix="/api/v1/ocr",
    tags=["OCR"]
)

app.include_router(
    llm_router,
    prefix="/api/v1/llm",
    tags=["LLM"]
)

app.include_router(
    orcamento_router,
    prefix="/api/v1/orcamentos",
    tags=["Orcamentos"]
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Loja API v2.0",
        "features": [
            "OCR assíncrono para notas fiscais",
            "Análise inteligente com LLM",
            "Sistema de transações de estoque",
            "Autenticação JWT",
            "API RESTful completa"
        ]
    }

@app.get("/ping", tags=["Health Check"])
def health_check():
    """Health check endpoint to verify if the API is running."""
    return {"status": "healthy", "message": "pong", "version": "2.0.0"}
