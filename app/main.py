"""Main application entry point.

This module creates and configures the FastAPI application, including exception handlers,
startup and shutdown events, and route inclusion.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.user_routes import router as user_router
from app.errors import BaseAppException
from app.utils.cache_util import _initialize_cache, cache
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI()


@app.exception_handler(BaseAppException)
async def base_app_exception_handler(_request: Request, exc: BaseAppException):
    """
    Handle BaseAppException by logging the error and returning a JSON error response.

    Args:
        _request (Request): The incoming request (unused).
        exc (BaseAppException): The exception instance.

    Returns:
        JSONResponse: The response containing error details.
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

    Args:
        _request (Request): The incoming request (unused).
        exc (Exception): The exception instance.

    Returns:
        JSONResponse: The response containing generic error details.
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


# Include the user router with a prefix and tags.
app.include_router(user_router, prefix="/api/users", tags=["users"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
