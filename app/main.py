from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.user_routes import router as user_router
from app.utils.cache_util import _initialize_cache, cache
from app.errors import BaseAppException
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI()

# 1) Handle your custom BaseAppException


@app.exception_handler(BaseAppException)
async def base_app_exception_handler(request: Request, exc: BaseAppException):
    # Log the exception with details
    logger.error(f"[BaseAppException] {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "details": exc.details,
        },
    )

# 2) Catch-all handler for any other uncaught exceptions


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("[Unhandled Exception]", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
            # For production, you might omit str(exc) to avoid leaking internal info
            "details": str(exc),
        },
    )


@app.on_event("startup")
async def startup_event():
    # Initialize the Redis cache when the application starts.
    await _initialize_cache()
    print("Redis cache initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    # Optionally, close the Redis connection on shutdown.
    if cache and cache.client:
        await cache.client.close()
        print("Redis connection closed.")

# Include your user router
app.include_router(user_router, prefix="/api/users", tags=["users"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
