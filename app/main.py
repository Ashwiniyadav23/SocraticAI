import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, seed_default_admin
from app.routers import (
    admin_router, auth_router, mentor_router, profile_router,
    reflection_router, session_router, speech_router, ws_router,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Socratic Learning Companion API",
    version="1.0.0",
    description="MVP backend implementing PRD Phase 1 (P0): Diagnostic + Socratic "
                 "Coach + hint ladder + basic mastery check + answer-leak guard.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
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
app.include_router(admin_router.router)


@app.on_event("startup")
async def on_startup():
    await init_db()
    await seed_default_admin()


@app.get("/health")
async def health():
    return {"status": "ok"}
