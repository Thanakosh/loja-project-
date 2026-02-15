import uuid
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.estoque import router as estoque_router
from app.api.v1.estoque_v2 import router as estoque_v2_router
from app.api.v1.llm import router as llm_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.orcamento import router as orcamento_router
from app.api.v1.produto import router as produto_router
from app.api.v1.users import router as users_router
from app.core.limiter import limiter
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.exceptions import BusinessException

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para gerenciamento de loja com OCR e IA",
    version="2.0.0"
)

app.state.limiter = limiter


@app.on_event("startup")
async def startup_warnings():
    """Warnings de segurança no startup da aplicação."""
    if "*" in settings.CORS_ORIGINS:
        logger.warning(
            "CORS wildcard ativo — não usar em produção"
        )
    logger.info(f"Loja API v2.0 iniciada | DEBUG={settings.DEBUG}")


@app.middleware("http")
async def add_trace_id_to_request(request: Request, call_next):
    request.state.trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Trace-Id"] = request.state.trace_id
    return response


def _error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details=None,
) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "details": details,
            "trace_id": trace_id,
        },
    )


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return _error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Erro HTTP"
    return _error_response(
        request=request,
        status_code=exc.status_code,
        code="http_error",
        message=message,
        details=detail,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(
        request=request,
        status_code=422,
        code="validation_error",
        message="Dados de requisição inválidos",
        details=exc.errors(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return _error_response(
        request=request,
        status_code=500,
        code="internal_server_error",
        message="Erro interno do servidor",
        details=None,
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return _error_response(
        request=request,
        status_code=429,
        code="rate_limit_exceeded",
        message="Limite de requisições excedido",
        details=f"Tente novamente em {exc.detail}" if hasattr(exc, "detail") else "Muitas requisições",
    )
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
