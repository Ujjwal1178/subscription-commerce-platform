"""Global Exception Handlers - Converts all exceptions to consistent JSON responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

import sys
sys.path.append("/app")
from shared.exceptions import AppException, ErrorCode
from app.logger import logger


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom AppException - converts to JSON response."""
    logger.warning(f"AppException: {exc.error_code} - {exc.message}")
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors - converts to user-friendly format."""
    errors = []
    for error in exc.errors():
        field = error["loc"][-1] if error["loc"] else "unknown"
        errors.append({"field": str(field), "message": error["msg"]})
    
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation failed. Please check your input.",
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "errors": errors
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler - logs full error, returns generic message."""
    logger.error(f"Unexpected error on {request.url.path}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred. Please try again later.",
            "error_code": ErrorCode.INTERNAL_ERROR.value
        }
    )


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
