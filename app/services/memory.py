import json
from redis.asyncio import Redis
from app.core.config import settings
from app.core.dependencies import get_redis_client

async def get_history(session_id: str) -> list[dict[str, str]]:
    raw = await get_redis_client().get(f"chat:{session_id}")
    return json.loads(raw) if raw else []

async def save_turn(session_id: str, history: list[dict[str, str]], user: str, assistant: str) -> None:
    history.extend([{"role": "user", "content": user}, {"role": "assistant", "content": assistant}])
    await get_redis_client().setex(
        f"chat:{session_id}", settings.CHAT_TTL_SECONDS, json.dumps(history[-20:])
    )
