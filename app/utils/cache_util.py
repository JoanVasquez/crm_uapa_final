import os
from typing import Optional

import redis.asyncio as redis

from app.errors import BaseAppException
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Cache:
    """
    A simple asynchronous cache interface wrapping Redis.
    """

    def __init__(self, client: redis.Redis):
        self.client = client

    async def set(self, key: str, value: str, ttl: int) -> None:
        """
        Set a key in Redis with an expiration (in seconds).
        """
        try:
            await self.client.set(key, value, ex=ttl)
        except Exception as error:
            logger.error(f"Redis set error for key '{key}': {error}", exc_info=True)
            raise BaseAppException(
                f"Redis set error for key '{key}': {error}"
            ) from error

    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis. Returns None if the key does not exist.
        """
        try:
            value = await self.client.get(key)
            return value.decode("utf-8") if value is not None else None
        except Exception as e:
            logger.error(f"Redis get error for key '{key}': {e}", exc_info=True)
            raise

    async def delete(self, key: str) -> None:
        """
        Delete a key from Redis.
        """
        try:
            await self.client.delete(key)
        except Exception as error:
            logger.error(f"Redis delete error for key '{key}': {error}", exc_info=True)
            raise BaseAppException(
                f"Redis delete error for key '{key}': {error}"
            ) from error


async def init_cache() -> Cache:
    """
    Initialize the Redis client using the URL from SSM (for production) or
    directly from an environment variable (for local/test) and return a Cache
    instance.
    """
    try:
        redis_url = None
        env = os.environ.get("DJANGO_ENV", "").lower()
        if env == "test":
            redis_url = os.environ.get("REDIS_URL_TEST")
        else:
            redis_url = os.environ.get("REDIS_URL")

        if not redis_url:
            raise BaseAppException(
                "Environment variable 'REDIS_URL | REDIS_URL_TEST' is not set"
            )
        logger.info(f"[init_cache] Using Redis URL: {redis_url}")
        client = redis.Redis.from_url(redis_url)
        await client.ping()
        logger.info("Redis client initialized successfully")
        return Cache(client)
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {e}", exc_info=True)
        raise BaseAppException(f"Failed to initialize Redis client: {e}") from e


# Global variable for the cache instance
cache: Optional[Cache] = None


async def _initialize_cache():
    """
    Asynchronously initialize the global cache.
    """
    global cache
    cache = await init_cache()
