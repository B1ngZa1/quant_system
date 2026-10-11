from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from enum import IntEnum

from app.core.logging import log as logger


class ErrorCode(IntEnum):
    SUCCESS = 0
    BUSINESS_ERROR = 4000
    UNAUTHORIZED = 4010
    INVALID_CREDENTIALS = 4011
    INVALID_TOKEN = 4012
    FORBIDDEN = 4030
    NOT_FOUND = 4040
    VALIDATION_ERROR = 4220
    SERVICE_UNAVAILABLE = 5030
    SERVER_ERROR = 5000


class BusinessException(Exception):
    def __init__(self, code: int = ErrorCode.BUSINESS_ERROR, message: str = "Business Error", status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


class DomainException(Exception):
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        logger.warning(f"Domain error: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=400,
            content={"code": 4000, "message": exc.message, "data": None},
        )
