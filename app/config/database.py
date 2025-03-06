import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.errors import BaseAppException
from app.utils.ssm_util import get_cached_parameter  # must be async!


async def init_engine():
    env = os.environ.get("DJANGO_ENV", "").lower()
    if env == "test":
        # For local development testing, use SQLite with aiosqlite.
        DATABASE_URL = "sqlite+aiosqlite:///./test.db"
        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    else:
        # Production / staging: use MySQL with SSM-fetched parameters.
        print("Using MySQL for production.")
        try:
            DB_NAME = await get_cached_parameter(os.getenv("DB_NAME"))
            DB_USER = await get_cached_parameter(os.getenv("DB_USER"))
            DB_PASSWORD = await get_cached_parameter(os.getenv("DB_PASSWORD"))
            DB_HOST = await get_cached_parameter(os.getenv("DB_HOST"))
            DB_PORT = await get_cached_parameter(os.getenv("DB_PORT"))
        except Exception as e:
            raise BaseAppException(
                "Failed to fetch DB parameters from SSM", details=str(e)
            ) from e

        # Use aiomysql as the async driver for MySQL.
        DATABASE_URL = (
            f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    return engine


# Initialize engine asynchronously. In an async application,
# you may want to await init_engine() during your app startup.
engine = asyncio.run(init_engine())

SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()
