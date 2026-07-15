import pytest
import time
from sqlalchemy import select, update
from app.database import db
from app.models import Prompt, PromptVersion, PromptEvaluationLog
from app.ai.prompts.service import PromptService

@pytest.mark.asyncio
async def test_prompt_version_manager(db_session):
    async with db.session_maker() as session:
        # Create prompt
        prompt = Prompt(name="test_prompt", description="A test prompt")
        session.add(prompt)
        
        # Create v1
        v1 = PromptVersion(
            prompt_name="test_prompt",
            version="1.0.0",
            template_text="Hello {{ learner_name }}, I am v1",
            input_schema={"type": "object", "properties": {"learner_name": {"type": "string"}}},
            is_active=True
        )
        session.add(v1)
        
        # Create v2
        v2 = PromptVersion(
            prompt_name="test_prompt",
            version="2.0.0",
            template_text="Greetings {{ learner_name }}, I am v2",
            input_schema={"type": "object", "properties": {"learner_name": {"type": "string"}}},
            is_active=False
        )
        session.add(v2)
        await session.commit()

    # Verify v1 is active
    rendered, version = await PromptService.render("test_prompt", {"learner_name": "Alice"})
    assert version == "1.0.0"
    assert "Hello Alice, I am v1" in rendered

    # Switch active version to v2
    async with db.session_maker() as session:
        await session.execute(update(PromptVersion).where(PromptVersion.version == "1.0.0").values(is_active=False))
        await session.execute(update(PromptVersion).where(PromptVersion.version == "2.0.0").values(is_active=True))
        await session.commit()

    # Verify v2 is active
    rendered, version = await PromptService.render("test_prompt", {"learner_name": "Bob"})
    assert version == "2.0.0"
    assert "Greetings Bob, I am v2" in rendered

@pytest.mark.asyncio
async def test_prompt_evaluation_logging(db_session):
    # Log a dummy execution
    await PromptService.log_evaluation(
        prompt_name="diagnostic",
        version="v1.2.3",
        tokens=150,
        cost=0.002,
        latency_ms=1200,
        success=True
    )
    
    async with db.session_maker() as session:
        stmt = select(PromptEvaluationLog).where(PromptEvaluationLog.prompt_id == "diagnostic")
        result = await session.execute(stmt)
        log_entry = result.scalars().first()
        
        assert log_entry is not None
        assert log_entry.version == "v1.2.3"
        assert log_entry.tokens_used == 150
        assert log_entry.latency_ms == 1200
        assert log_entry.success is True
