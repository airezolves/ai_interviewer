"""Global error handling middleware for FastAPI services."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from shared.utils.logger import get_logger

logger = get_logger(__name__)


class ServiceException(Exception):
    """Base exception for service errors."""

    def __init__(self, message: str, status_code: int = 400, detail: str | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundException(ServiceException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            detail=f"{resource} with id '{resource_id}' does not exist",
        )


class UnauthorizedException(ServiceException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(ServiceException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, status_code=403)


class RateLimitException(ServiceException):
    def __init__(self):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            detail="Too many requests. Please try again later.",
        )


class UsageLimitException(ServiceException):
    def __init__(self, plan: str = "free"):
        super().__init__(
            message="Usage limit reached",
            status_code=403,
            detail=f"You've reached your {plan} plan limit. Upgrade to continue.",
        )


def register_error_handlers(app):
    """Register global error handlers on a FastAPI app."""

    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        logger.error("service_error", message=exc.message, status_code=exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation error",
                "detail": str(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_error", error=str(exc), type=type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc) if not request.app.state.is_production else None,
            },
        )
