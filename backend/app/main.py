import contextvars
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.estoque import router as estoque_router
from app.api.v1.estoque_v2 import router as estoque_v2_router
from app.api.v1.llm import router as llm_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.orcamento import router as orcamento_router
from app.api.v1.produto import router as produto_router
from app.api.v1.users import router as users_router
from app.api.v1.clientes import router as clientes_router
from app.api.v1.vendas import router as vendas_router
from app.api.v1.movimentacao import router as movimentacao_router
from app.core.limiter import limiter

from .core.config import settings
from .core.error_handlers import register_exception_handlers
from .core.logging_config import setup_logging

setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

_trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para gerenciamento de loja com OCR e IA",
    version="2.0.0"
)

app.state.limiter = limiter
register_exception_handlers(app)


@app.on_event("startup")
async def startup_warnings():
    """Warnings de segurança no startup da aplicação."""
    environment = settings.ENVIRONMENT.lower()

    if "*" in settings.CORS_ORIGINS:
        logger.warning(
            "CORS wildcard ativo — não usar em produção"
        )

    if environment == "production" and settings.DEBUG:
        logger.warning(
            "⚠️  DEBUG=True em produção detectado. Isso aumenta risco de exposição de informações sensíveis."
        )

    if environment == "production" and settings.LOG_LEVEL.upper() == "DEBUG":
        logger.warning(
            "⚠️  LOG_LEVEL=DEBUG em produção pode expor dados sensíveis e aumentar ruído operacional."
        )

    if environment in {"staging", "production"} and settings.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
        logger.warning(
            "⚠️  ACCESS_TOKEN_EXPIRE_MINUTES acima de 60 em staging/production. "
            "Considere reduzir a duração para diminuir impacto de comprometimento de token."
        )

    logger.info(f"Loja API v2.0 iniciada | DEBUG={settings.DEBUG}")


@app.middleware("http")
async def add_trace_id_to_request(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    request.state.trace_id = trace_id
    token = _trace_id_ctx.set(trace_id)

    logger.info(
        "Request iniciada",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": str(request.url.path),
        },
    )

    try:
        response = await call_next(request)
    finally:
        _trace_id_ctx.reset(token)

    response.headers["X-Trace-Id"] = trace_id
    logger.info(
        "Request concluída",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
        },
    )
    return response


# Se CORS_ORIGINS for ["*"], allow_credentials DEVE ser False
allow_credentials = "*" not in settings.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(estoque_router, prefix="/api/v1/estoque", tags=["Estoque (Legado)"])
app.include_router(estoque_v2_router, prefix="/api/v2/estoque", tags=["Estoque V2"])
app.include_router(produto_router, prefix="/api/v1/produtos", tags=["Produtos"])
app.include_router(ocr_router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(llm_router, prefix="/api/v1/llm", tags=["LLM"])
app.include_router(orcamento_router, prefix="/api/v1/orcamentos", tags=["Orcamentos"])
app.include_router(clientes_router, prefix="/api/v1/clientes", tags=["Clientes (Histórico)"])
app.include_router(vendas_router, prefix="/api/v1/vendas", tags=["Vendas (Histórico)"])
app.include_router(movimentacao_router, prefix="/api/v1/movimentacao", tags=["Estoque - Movimentação"])


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
