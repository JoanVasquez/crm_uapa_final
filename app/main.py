from fastapi import FastAPI
from app.api.user_routes import router as user_router
from app.utils.cache_util import _initialize_cache, cache

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    # Initialize the Redis cache when the application starts.
    await _initialize_cache()
    # Optionally, you can log or test the connection here.
    print("Redis cache initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    # Optionally, close the Redis connection on shutdown.
    if cache and cache.client:
        await cache.client.close()
        print("Redis connection closed.")

app.include_router(user_router, prefix="/api/users", tags=["users"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
