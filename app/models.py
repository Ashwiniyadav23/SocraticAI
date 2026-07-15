import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def uuid_pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="student")  # student|mentor
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SemanticMemory(Base):
    __tablename__ = "semantic_memory"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    learning_style: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation_style: Mapped[str | None] = mapped_column(String, nullable=True)
    language_preference: Mapped[str | None] = mapped_column(String, nullable=True)
    strong_topics: Mapped[list] = mapped_column(JSON, default=list)
    weak_topics: Mapped[list] = mapped_column(JSON, default=list)
    behavioral_traits: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ShortTermMemory(Base):
    __tablename__ = "short_term_memory"
    thread_id: Mapped[str] = mapped_column(String, primary_key=True)
    checkpoint_id: Mapped[str] = mapped_column(String, primary_key=True)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkingMemory(Base):
    __tablename__ = "working_memory"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    active_concepts: Mapped[list] = mapped_column(JSON, default=list)
    current_learning_objective_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_goals.id"), nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String, index=True)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)
    canonical_facts: Mapped[dict] = mapped_column(JSON, default=dict)  # {"fact_id": "text", ...}
    domain: Mapped[str] = mapped_column(String, default="dsa")


class Mastery(Base):
    __tablename__ = "mastery"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"))
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retention_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LearningSession(Base):
    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"))
    context_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("session_contexts.id", use_alter=True, name="fk_session_context"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_state: Mapped[str | None] = mapped_column(String, nullable=True)
    current_state: Mapped[str] = mapped_column(String, default="UNKNOWN")
    current_mode: Mapped[str | None] = mapped_column(String, nullable=True)
    hint_tier: Mapped[int] = mapped_column(Integer, default=0)
    unresolved_turns: Mapped[int] = mapped_column(Integer, default=0)

    turns: Mapped[list["SessionTurn"]] = relationship(back_populates="session")


class SessionTurn(Base):
    __tablename__ = "session_turns"
    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    role: Mapped[str] = mapped_column(String)  # student|tutor
    content: Mapped[str] = mapped_column(Text)
    mode: Mapped[str | None] = mapped_column(String, nullable=True)
    hint_tier: Mapped[int | None] = mapped_column(Integer, nullable=True)
    learner_state: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["LearningSession"] = relationship(back_populates="turns")


from pgvector.sqlalchemy import Vector


class MemoryFact(Base):
    """Concept-graph canonical fact used for misconception checking (Section 12)."""
    __tablename__ = "memory_facts"
    id: Mapped[uuid.UUID] = uuid_pk()
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HintLog(Base):
    __tablename__ = "hints_log"
    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    tier: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String)
    was_leak_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reflection(Base):
    __tablename__ = "reflections"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"))
    teach_back_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"))
    assessment_type: Mapped[str] = mapped_column(String)  # transfer|tracing|prediction
    input: Mapped[str] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EpisodicMemory(Base):
    """Semantic summaries of specific past interactions or breakthroughs."""
    __tablename__ = "episodic_memory"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String)  # breakthrough, struggle, analogy_used, anti_pattern
    description: Mapped[str] = mapped_column(Text)
    context_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningJourney(Base):
    """Timeline of major milestones."""
    __tablename__ = "learning_journey"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    milestone_type: Mapped[str] = mapped_column(String)  # concept_mastered, goal_achieved, streak_reached
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningGoal(Base):
    """Student-defined goals."""
    __tablename__ = "learning_goals"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_concepts: Mapped[list] = mapped_column(JSON, default=list)  # list of concept_id strings
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Prompt(Base):
    __tablename__ = "prompts"
    name: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    id: Mapped[uuid.UUID] = uuid_pk()
    prompt_name: Mapped[str] = mapped_column(String, ForeignKey("prompts.name"))
    version: Mapped[str] = mapped_column(String)  # e.g. "1.0.0"
    template_text: Mapped[str] = mapped_column(Text)
    input_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PromptEvaluationLog(Base):
    __tablename__ = "prompt_evaluation_logs"
    id: Mapped[uuid.UUID] = uuid_pk()
    prompt_id: Mapped[str] = mapped_column(String, ForeignKey("prompts.name"))
    version: Mapped[str] = mapped_column(String)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionLog(Base):
    __tablename__ = "decision_logs"
    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    turn_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("session_turns.id"), nullable=True)
    inputs_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    decision_output: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionContext(Base):
    __tablename__ = "session_contexts"
    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    purpose: Mapped[str] = mapped_column(String)
    urgency: Mapped[str] = mapped_column(String)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_depth: Mapped[str] = mapped_column(String)
    objective: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EducationalDocumentChunk(Base):
    __tablename__ = "educational_chunks"
    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[str] = mapped_column(String, index=True)
    topic: Mapped[str] = mapped_column(String, index=True)
    difficulty_level: Mapped[int] = mapped_column(Integer)
    format: Mapped[str] = mapped_column(String)
    language: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    source_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
