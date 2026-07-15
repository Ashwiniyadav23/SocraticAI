import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import settings

_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_pool)


SESSION_TTL_SECONDS = 60 * 60 * 12  # 12h, per PRD Section 12 (Session memory, Redis TTL)


async def get_working_memory(session_id: str) -> dict:
    r = get_redis()
    raw = await r.get(f"working:{session_id}")
    if not raw:
        return {"messages": [], "mode": None, "hint_tier": 0}
    return json.loads(raw)


async def set_working_memory(session_id: str, data: dict) -> None:
    r = get_redis()
    await r.set(f"working:{session_id}", json.dumps(data), ex=SESSION_TTL_SECONDS)


async def append_message(session_id: str, role: str, content: str, max_keep: int = 12) -> None:
    mem = await get_working_memory(session_id)
    mem["messages"].append({"role": role, "content": content})
    mem["messages"] = mem["messages"][-max_keep:]
    await set_working_memory(session_id, mem)
