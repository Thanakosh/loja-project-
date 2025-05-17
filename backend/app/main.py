from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.estoque import router as estoque_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.users import router as users_router
from app.api.v1.llm import router as llm_router
from app.api.v1.orcamento import router as orcamento_router
from app.schemas.llm import LLMRequest, LLMResponse
from .core.config import settings

app = FastAPI(
    title=settings.project_name,
    description="API para gerenciamento de loja",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(
    estoque_router,
    prefix="/api/v1/estoque",
    tags=["Estoque"]
)

app.include_router(
    ocr_router,
    prefix="/api/v1/ocr",
    tags=["OCR"]
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"]
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
    return {"message": "Welcome to Loja API"}

@app.get("/ping", tags=["Health Check"])
def health_check():
    """
    Health check endpoint to verify if the API is running.
    """
    return {"status": "healthy", "message": "pong"}