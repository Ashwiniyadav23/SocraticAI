import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import auth_router, mentor_router, profile_router, reflection_router, session_router, ws_router, speech_router, rag_router

logging.basicConfig(level=logging.INFO)

from contextlib import asynccontextmanager
from app.config import settings
from app.database import db, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init(settings.DATABASE_URL)
    await init_db()
    yield
    await db.close()

app = FastAPI(
    title="Socratic Learning Companion API",
    version="1.0.0",
    description="MVP backend implementing PRD Phase 1 (P0): Diagnostic + Socratic "
                 "Coach + hint ladder + basic mastery check + answer-leak guard.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(session_router.router)
app.include_router(profile_router.router)
app.include_router(reflection_router.router)
app.include_router(mentor_router.router)
app.include_router(ws_router.router)
app.include_router(speech_router.router)
app.include_router(rag_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
