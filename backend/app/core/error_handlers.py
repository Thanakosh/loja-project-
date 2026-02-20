import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import BusinessException

logger = logging.getLogger(__name__)


def _build_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
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


def _http_error_code(status_code: int) -> str:
    mapping = {
        401: "unauthorized",
        403: "forbidden",
        404: "resource_not_found",
        405: "method_not_allowed",
    }
    return mapping.get(status_code, "http_error")


def _extract_message(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict) and isinstance(detail.get("message"), str):
        return detail["message"]
    return "Erro HTTP"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        logger.warning(
            "Business exception capturada",
            extra={"trace_id": getattr(request.state, "trace_id", ""), "code": exc.code},
        )
        return _build_error_response(
            request=request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        return _build_error_response(
            request=request,
            status_code=exc.status_code,
            code="http_error",
            message=_extract_message(detail),
            details=detail,
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        return _build_error_response(
            request=request,
            status_code=exc.status_code,
            code=_http_error_code(exc.status_code),
            message=_extract_message(detail),
            details=detail,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return _build_error_response(
            request=request,
            status_code=422,
            code="validation_error",
            message="Dados de requisição inválidos",
            details=exc.errors(),
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        retry_after = None
        if hasattr(exc, "headers") and isinstance(exc.headers, dict):
            retry_after = exc.headers.get("Retry-After") or exc.headers.get("retry-after")
        if retry_after is None and hasattr(exc, "detail"):
            retry_after = str(exc.detail)

        response = _build_error_response(
            request=request,
            status_code=429,
            code="rate_limit_exceeded",
            message="Limite de requisições excedido",
            details=f"Tente novamente em {exc.detail}" if hasattr(exc, "detail") else "Muitas requisições",
        )
        if retry_after is not None:
            response.headers["Retry-After"] = str(retry_after)
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Erro não tratado na aplicação",
            extra={"trace_id": getattr(request.state, "trace_id", "")},
        )
        return _build_error_response(
            request=request,
            status_code=500,
            code="internal_server_error",
            message="Erro interno do servidor",
            details=None,
        )
