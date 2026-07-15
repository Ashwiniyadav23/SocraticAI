import pytest
from app.ai.context.models import LearningContext
from app.ai.context.adapter import adapt_pedagogy
from app.ai.context.detector import detect_context
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_detect_context_fallback():
    # Test fallback behavior on exception
    with patch("app.ai.context.detector.chat", side_effect=Exception("API Error")):
        ctx = await detect_context("I want to learn", [])
        assert ctx.purpose == "General Learning"
        assert ctx.urgency == "Low"

@pytest.mark.asyncio
async def test_detect_context_success():
    mock_response = '{"purpose": "Interview Prep", "urgency": "High", "expected_depth": "Functional", "objective": "React Hooks"}'
    with patch("app.ai.context.detector.chat", return_value=mock_response):
        ctx = await detect_context("I have an interview tomorrow!", [])
        assert ctx.purpose == "Interview Prep"
        assert ctx.urgency == "High"
        assert ctx.objective == "React Hooks"

def test_adapt_pedagogy():
    ctx = LearningContext(purpose="Exam", urgency="High", expected_depth="Surface", objective="Pass")
    config = adapt_pedagogy(ctx)
    assert config["tutor_mode_override"] == "socratic_assessor"
    assert config["hint_strategy"] == "direct"
    assert config["suppress_curiosity"] is True
    assert config["resource_recommendation"] == "cheat_sheets"

def test_adapt_pedagogy_curiosity():
    ctx = LearningContext(purpose="Curiosity", urgency="Low", expected_depth="Deep", objective="Explore")
    config = adapt_pedagogy(ctx)
    assert config["tutor_mode_override"] == "exploratory_guide"
    assert config["hint_strategy"] == "deep_socratic"
    assert config["suppress_curiosity"] is False
