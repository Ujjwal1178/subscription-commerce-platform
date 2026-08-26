"""
Global Exception Handlers for Auth Service

Converts all exceptions to consistent JSON response format:
{
    "success": false,
    "message": "Human readable error",
    "error_code": "MACHINE_READABLE_CODE",
    ...additional fields
}

This ensures frontend always receives same structure regardless of error type.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

import sys
sys.path.append("/app")
from shared.exceptions import AppException, ErrorCode
from app.logger import logger


# =============================================================================
# APP EXCEPTION HANDLER
# =============================================================================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle our custom AppException.
    
    Converts AppException to consistent JSON response.
    """
    logger.warning(
        f"AppException: {exc.error_code} - {exc.message}",
        extra={"path": request.url.path, "error_code": exc.error_code}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


# =============================================================================
# VALIDATION ERROR HANDLER (Pydantic)
# =============================================================================

async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Converts complex Pydantic errors to simple, user-friendly format.
    
    Before:
        {"detail": [{"loc": ["body", "email"], "msg": "field required", ...}]}
    
    After:
        {
            "success": false,
            "message": "Validation failed",
            "error_code": "VALIDATION_ERROR",
            "errors": [{"field": "email", "message": "field required"}]
        }
    """
    errors = []
    
    for error in exc.errors():
        # Extract field name (last item in location)
        field = error["loc"][-1] if error["loc"] else "unknown"
        
        # Clean up message
        message = error["msg"]
        
        errors.append({
            "field": str(field),
            "message": message
        })
    
    logger.warning(
        f"Validation error on {request.url.path}: {errors}",
        extra={"path": request.url.path, "errors": errors}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation failed. Please check your input.",
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "errors": errors
        }
    )


# =============================================================================
# GENERIC EXCEPTION HANDLER (Catch-all)
# =============================================================================

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.
    
    - Logs full error for debugging
    - Returns generic message to user (security - don't expose internals)
    """
    logger.error(
        f"Unexpected error on {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred. Please try again later.",
            "error_code": ErrorCode.INTERNAL_ERROR.value
        }
    )


# =============================================================================
# HELPER: Register all handlers
# =============================================================================

def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app.
    
    Call this in main.py:
        from app.exception_handlers import register_exception_handlers
        register_exception_handlers(app)
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
