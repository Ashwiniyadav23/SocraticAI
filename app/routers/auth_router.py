from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import LearnerProfile, User
from app.schemas import GoogleToken, Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    status = "active" if payload.role != "mentor" else "pending"
    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=payload.role, status=status)
    db.add(user)
    await db.flush()
    db.add(LearnerProfile(user_id=user.id))
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="Account pending approval")
    if user.status == "suspended":
        raise HTTPException(status_code=403, detail="Account suspended")
    return Token(access_token=create_access_token(user.id))


import httpx

@router.post("/google", response_model=Token)
async def google_auth(payload: GoogleToken, db: AsyncSession = Depends(get_db)):
    try:
        # Verify the access token by fetching user info
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {payload.token}"}
            )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google token")
            
        idinfo = response.json()
        email = idinfo.get("email")
        
        if not email:
            raise HTTPException(status_code=400, detail="Invalid Google token")

        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            # Create a new user without a password
            user = User(email=email, hashed_password=None, role="student")
            db.add(user)
            await db.flush()
            db.add(LearnerProfile(user_id=user.id))
            await db.commit()
            await db.refresh(user)
        
        return Token(access_token=create_access_token(user.id))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")
