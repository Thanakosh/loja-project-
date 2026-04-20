import contextvars
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.estoque import router as estoque_router
from app.api.v1.estoque_v2 import router as estoque_v2_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.orcamento import router as orcamento_router
from app.api.v1.produto import router as produto_router
from app.api.v1.users import router as users_router
from app.api.v1.categorias import router as categorias_router
from app.api.v1.clientes import router as clientes_router
from app.api.v1.vendas import router as vendas_router
from app.api.v1.pdv import router as pdv_router
from app.api.v1.movimentacao import router as movimentacao_router
from app.api.v1.fornecedores import router as fornecedores_router
from app.api.v1.contas_receber import router as contas_receber_router
from app.api.v1.notas_fiscais import router as notas_fiscais_router
from app.api.v1.relatorios import router as relatorios_router
from app.api.v1.caixa import router as caixa_router
from app.api.v1.politica_desconto import router as politica_desconto_router
from app.api.v1.fiscal_ai import router as fiscal_ai_router
from app.api.v1.configuracoes import router as configuracoes_router
from app.api.v1.ai import router as ai_router
from app.api.v1.health_async import router as health_router
from app.api.endpoints.ncm import router as ncm_router
from app.core.desktop_bootstrap import bootstrap_desktop_database
from app.core.limiter import limiter

from .core.config import settings
from .core.error_handlers import register_exception_handlers
from .core.logging_config import setup_logging

setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

_trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # — startup —
    environment = settings.ENVIRONMENT.lower()
    app.state.desktop_initial_admin = await bootstrap_desktop_database()

    if "*" in settings.CORS_ORIGINS:
        logger.warning("CORS wildcard ativo — não usar em produção")

    if environment == "production" and settings.DEBUG:
        logger.warning("⚠️  DEBUG=True em produção detectado.")

    if environment == "production" and settings.LOG_LEVEL.upper() == "DEBUG":
        logger.warning("⚠️  LOG_LEVEL=DEBUG em produção pode expor dados sensíveis.")

    if environment in {"staging", "production"} and settings.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
        logger.warning("⚠️  ACCESS_TOKEN_EXPIRE_MINUTES acima de 60 em staging/production.")

    logger.info(f"Loja API v2.0 iniciada | DEBUG={settings.DEBUG}")
    yield
    # — shutdown (adicionar lógica futura aqui se necessário) —

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para gerenciamento de loja. Importação de notas fiscais via XML de NFe.",
    version="2.1.1",
    lifespan=lifespan,
)

app.state.limiter = limiter
register_exception_handlers(app)

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

    # Headers de depreciação para endpoints legados (RFC 8594)
    path = str(request.url.path)
    if path.startswith("/api/v1/estoque"):
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "Mon, 01 Sep 2026 00:00:00 GMT"
        response.headers["Link"] = '</api/v2/estoque>; rel="successor-version"'

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
app.include_router(orcamento_router, prefix="/api/v1/orcamentos", tags=["Orcamentos"])
app.include_router(clientes_router, prefix="/api/v1/clientes", tags=["Clientes (Histórico)"])
app.include_router(categorias_router, prefix="/api/v1/categorias", tags=["Categorias"])
app.include_router(vendas_router, prefix="/api/v1/vendas", tags=["Vendas (Histórico)"])
app.include_router(pdv_router, prefix="/api/v1/pdv", tags=["PDV"])
app.include_router(movimentacao_router, prefix="/api/v1/movimentacao", tags=["Estoque - Movimentação"])
app.include_router(fornecedores_router, prefix="/api/v1/fornecedores", tags=["Fornecedores"])
app.include_router(contas_receber_router, prefix="/api/v1/contas-receber", tags=["Contas a Receber"])
app.include_router(notas_fiscais_router, prefix="/api/v1/notas-fiscais", tags=["Notas Fiscais"])
app.include_router(relatorios_router, prefix="/api/v1/relatorios", tags=["Relatórios"])
app.include_router(caixa_router, prefix="/api/v1/caixa", tags=["Caixa Diário"])
app.include_router(politica_desconto_router, prefix="/api/v1/politica-desconto", tags=["Política de Desconto"])
app.include_router(configuracoes_router, prefix="/api/v1/configuracoes", tags=["Configuracoes"])
app.include_router(ncm_router, prefix="/api/v1/ncm", tags=["NCM"])
app.include_router(fiscal_ai_router, prefix="/api/v1/fiscal-ai", tags=["Fiscal AI"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(health_router, prefix="/api/v2", tags=["Health"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to Loja API v2.1",
        "features": [
            "Importação de notas fiscais via XML de NFe",
            "Sistema de transações de estoque",
            "Autenticação JWT",
            "API RESTful completa"
        ],
        "coming_soon": [
            "OCR de imagens e PDFs via IA",
        ]
    }


@app.get("/ping", tags=["Health Check"])
def health_check():
    """Health check endpoint to verify if the API is running."""
    return {"status": "healthy", "message": "pong", "version": "2.1.1"}
