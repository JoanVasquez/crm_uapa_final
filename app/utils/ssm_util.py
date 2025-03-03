import asyncio
import functools
import os

import boto3
from botocore.exceptions import ClientError

from app.errors import BaseAppException
from app.utils.cache_util import cache
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def get_cached_parameter(name: str, ttl: int = 3600) -> str:
    """
    Fetch an SSM parameter value with caching in Redis.

    In local or test environments, returns the value from an environment variable.
    In production, first checks Redis. If the value is not cached, fetches it from AWS SSM,
    caches it for `ttl` seconds, and then returns the value.
    """
    env = os.environ.get("DJANGO_ENV", "").lower()
    if env == "test":
        # For local/test environments, use the environment variable directly.
        value = os.environ.get(name)
        if value is None:
            raise BaseAppException(f"Environment variable '{name}' is not set")
        logger.info(
            f"[get_cached_parameter] Using environment variable '{name}': {value}"
        )
        return value

    # Try to retrieve the parameter from Redis.
    cached_value = await cache.get(name)
    if cached_value is not None:
        logger.info(f"[get_cached_parameter] Returning cached parameter for '{name}'")
        return cached_value

    # If not found in cache, fetch from AWS SSM.
    ssm_client = boto3.client("ssm")
    try:
        logger.info(f"[get_cached_parameter] Fetching parameter '{name}' from SSM")
        # Run the synchronous boto3 call in an executor.
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            functools.partial(ssm_client.get_parameter, Name=name, WithDecryption=True),
        )
        value = response["Parameter"]["Value"]
        # Cache the retrieved parameter in Redis.
        await cache.set(name, value, ttl)
        return value
    except ClientError as error:
        logger.error(
            f"[get_cached_parameter] Error fetching parameter '{name}' from SSM: {error}",
            exc_info=True,
        )
        raise BaseAppException(f"Could not fetch parameter: {name}") from error
