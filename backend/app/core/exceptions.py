from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import logging
from enum import IntEnum

logger = logging.getLogger(__name__)

class ErrorCode(IntEnum):
    SUCCESS = 0
    BUSINESS_ERROR = 4000
    UNAUTHORIZED = 4010
    FORBIDDEN = 4030
    NOT_FOUND = 4040
    VALIDATION_ERROR = 4220
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
            content={"error_code": exc.code, "message": exc.message}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}
        )
