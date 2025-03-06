"""
Main application entry point.

This module creates and configures the FastAPI application, including exception handlers,
startup and shutdown events, and route inclusion.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.bill_routes import router as bill_router
from app.api.product_routes import router as product_router
from app.api.sell_routes import router as sell_router

# Import all your routers
from app.api.user_routes import router as user_router
from app.errors import BaseAppException
from app.utils.cache_util import _initialize_cache, cache
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create the FastAPI app instance with custom metadata for Swagger
app = FastAPI(
    title="CRM Python Simple API",
    description="API for managing users, bills, products, and sell transactions.",
    version="0.1.0",
    docs_url="/docs",  # Swagger UI (default)
    redoc_url="/redoc",  # Redoc (default)
    openapi_url="/openapi.json",  # OpenAPI schema URL
)

_API_PREFIX = "/api/v1"

# Include your routes under the prefix /api/v1
app.include_router(user_router, prefix=_API_PREFIX)
app.include_router(bill_router, prefix=_API_PREFIX)
app.include_router(product_router, prefix=_API_PREFIX)
app.include_router(sell_router, prefix=_API_PREFIX)


@app.exception_handler(BaseAppException)
async def base_app_exception_handler(_request: Request, exc: BaseAppException):
    """
    Handle BaseAppException by logging the error and returning a JSON error response.
    """
    logger.error("[BaseAppException] %s", exc.message, exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_request: Request, exc: Exception):
    """
    Handle uncaught exceptions by logging the error and returning a generic JSON error response.
    """
    logger.error("[Unhandled Exception]", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
            "details": str(exc),
        },
    )


@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event handler.

    Initializes the Redis cache when the application starts.
    """
    await _initialize_cache()
    print("Redis cache initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    FastAPI shutdown event handler.

    Closes the Redis connection when the application shuts down.
    """
    if cache and cache.client:
        await cache.client.close()
        print("Redis connection closed.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
