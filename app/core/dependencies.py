
from functools import lru_cache

from redis.asyncio import Redis
from qdrant_client import AsyncQdrantClient

from app.core.config import settings


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_resources() -> None:
    await get_qdrant_client().close()
    await get_redis_client().aclose()
