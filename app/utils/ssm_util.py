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

    In local or test environments, return the value from an environment variable.
    In production, check the cache and then fetch from AWS SSM if necessary.
    """
    env = os.environ.get("DJANGO_ENV", "").lower()
    if env in ["test", "dev"]:
        # Use environment variable directly
        value = os.environ.get(name)
        if value is None:
            raise BaseAppException(f"Environment variable '{name}' is not set")
        logger.info(
            f"[get_cached_parameter] Using environment variable '{name}': {value}"
        )
        return value

    # For production: try the cache first
    cached_value = await cache.get(name)
    if cached_value is not None:
        logger.info(f"[get_cached_parameter] Returning cached parameter for '{name}'")
        return cached_value

    # Not in cache; fetch from AWS SSM
    ssm_client = boto3.client("ssm")
    try:
        logger.info(f"[get_cached_parameter] Fetching parameter '{name}' from SSM")
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            functools.partial(ssm_client.get_parameter, Name=name, WithDecryption=True),
        )
        value = response["Parameter"]["Value"]
        await cache.set(name, value, ttl)
        return value
    except ClientError as error:
        logger.error(
            f"[get_cached_parameter] Error fetching parameter '{name}' from SSM: {error}",
            exc_info=True,
        )
        raise BaseAppException(f"Could not fetch parameter: {name}") from error
