"""Token decoding helper for WebSocket auth (query-param token, since WS can't
send Authorization headers from a browser easily)."""
import uuid

from jose import JWTError, jwt
from sqlalchemy import select

from app.config import settings
from app.database import db
from app.models import User


async def get_user_from_token(token: str) -> User | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    async with db.session_maker() as db_session:
        result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()
