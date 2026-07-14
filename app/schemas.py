import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "student"


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionCreate(BaseModel):
    concept_name: str


class SessionOut(BaseModel):
    id: uuid.UUID
    concept_id: uuid.UUID
    current_state: str
    current_mode: str | None
    hint_tier: int

    class Config:
        from_attributes = True


class TurnCreate(BaseModel):
    message: str


class TurnOut(BaseModel):
    session_id: uuid.UUID
    tutor_message: str
    learner_state: str
    mode: str
    hint_tier: int
    leak_guard_triggered: bool = False


class StateOut(BaseModel):
    session_id: uuid.UUID
    learner_state: str
    mode: str | None
    hint_tier: int


class ReflectionCreate(BaseModel):
    concept_name: str
    teach_back_text: str


class MasteryOut(BaseModel):
    concept_id: uuid.UUID
    mastery_score: float
    evidence_breakdown: dict
    last_assessed_at: datetime | None
    retention_due_at: datetime | None

    class Config:
        from_attributes = True


class MentorOverride(BaseModel):
    student_id: uuid.UUID
    concept_name: str
    forced_mode: str
