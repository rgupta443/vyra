"""
Comprehensive error handling middleware for the application.

This middleware provides centralized error handling, logging, and
user-friendly error responses across all API endpoints.

Validates Requirements 16.1, 16.2, 16.3
"""
import logging
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format."""
    
    def __init__(
        self,
        message: str,
        status_code: int,
        error_type: str = "error",
        details: dict = None,
        request_id: str = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        self.request_id = request_id
    
    def to_dict(self):
        """Convert to dictionary for JSON response."""
        response = {
            "error": self.error_type,
            "message": self.message,
            "status_code": self.status_code,
        }
        
        if self.details:
            response["details"] = self.details
        
        if self.request_id:
            response["request_id"] = self.request_id
        
        return response


class ErrorHandlerMiddleware:
    """
    Middleware for comprehensive error handling.
    
    Catches all exceptions and converts them to standardized error responses
    with appropriate logging and user-friendly messages.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            # Handle the exception and send error response
            request = Request(scope, receive)
            response = await self.handle_exception(request, exc)
            await response(scope, receive, send)
    
    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """
        Handle different types of exceptions and return appropriate responses.
        
        Args:
            request: The incoming request
            exc: The exception that occurred
            
        Returns:
            JSONResponse with error details
        """
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # Log the exception with context
        logger.error(
            f"Exception occurred: {type(exc).__name__}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "exception": str(exc),
                "traceback": traceback.format_exc()
            }
        )
        
        # Handle specific exception types
        if isinstance(exc, StarletteHTTPException):
            return self._handle_http_exception(exc, request_id)
        
        elif isinstance(exc, RequestValidationError):
            return self._handle_validation_error(exc, request_id)
        
        elif isinstance(exc, ValidationError):
            return self._handle_pydantic_validation_error(exc, request_id)
        
        elif isinstance(exc, IntegrityError):
            return self._handle_integrity_error(exc, request_id)
        
        elif isinstance(exc, SQLAlchemyError):
            return self._handle_database_error(exc, request_id)
        
        else:
            return self._handle_generic_error(exc, request_id)
    
    def _handle_http_exception(
        self, exc: StarletteHTTPException, request_id: str
    ) -> JSONResponse:
        """Handle HTTP exceptions from FastAPI/Starlette."""
        error = ErrorResponse(
            message=exc.detail,
            status_code=exc.status_code,
            error_type="http_error",
            request_id=request_id
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error.to_dict()
        )
    
    def _handle_validation_error(
        self, exc: RequestValidationError, request_id: str
    ) -> JSONResponse:
        """Handle request validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        error = ErrorResponse(
            message="Validation error in request data",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="validation_error",
            details={"errors": errors},
            request_id=request_id
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error.to_dict()
        )
    
    def _handle_pydantic_validation_error(
        self, exc: ValidationError, request_id: str
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        error = ErrorResponse(
            message="Data validation error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="validation_error",
            details={"errors": errors},
            request_id=request_id
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error.to_dict()
        )
    
    def _handle_integrity_error(
        self, exc: IntegrityError, request_id: str
    ) -> JSONResponse:
        """Handle database integrity constraint violations."""
        # Extract useful information from the error
        error_message = "Database constraint violation"
        
        if "unique" in str(exc).lower():
            error_message = "A record with this information already exists"
        elif "foreign key" in str(exc).lower():
            error_message = "Referenced record does not exist"
        elif "not null" in str(exc).lower():
            error_message = "Required field is missing"
        
        error = ErrorResponse(
            message=error_message,
            status_code=status.HTTP_409_CONFLICT,
            error_type="integrity_error",
            request_id=request_id
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error.to_dict()
        )
    
    def _handle_database_error(
        self, exc: SQLAlchemyError, request_id: str
    ) -> JSONResponse:
        """Handle general database errors."""
        logger.error(f"Database error: {exc}", extra={"request_id": request_id})
        
        error = ErrorResponse(
            message="A database error occurred. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="database_error",
            request_id=request_id
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error.to_dict()
        )
    
    def _handle_generic_error(
        self, exc: Exception, request_id: str
    ) -> JSONResponse:
        """Handle unexpected errors."""
        logger.error(
            f"Unexpected error: {exc}",
            extra={
                "request_id": request_id,
                "traceback": traceback.format_exc()
            }
        )
        
        error = ErrorResponse(
            message="An unexpected error occurred. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="internal_error",
            request_id=request_id
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error.to_dict()
        )


async def add_request_id_middleware(request: Request, call_next: Callable):
    """
    Middleware to add unique request ID to all requests.
    
    This helps with tracking and debugging requests across the system.
    """
    import uuid
    
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    # Add request ID to request state for access in endpoints
    request.state.request_id = request_id
    
    # Process the request
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response
