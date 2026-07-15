import pytest
from app.ai.prompts.service import PromptService, PromptNotFoundError

@pytest.mark.asyncio
async def test_load_existing_prompt():
    prompt = await PromptService.load_prompt("diagnostic")
    assert prompt["name"] == "diagnostic"
    assert "input_schema" in prompt
    assert "template" in prompt

@pytest.mark.asyncio
async def test_load_non_existent_prompt():
    with pytest.raises(PromptNotFoundError):
        await PromptService.load_prompt("does_not_exist")

@pytest.mark.asyncio
async def test_render_prompt_with_valid_schema():
    # socratic_tutor requires tutor_mode
    rendered, version = await PromptService.render("socratic_tutor", {"tutor_mode": "FOUNDATION_BUILDER"})
    assert "Foundation Builder" in rendered
    assert "HARD CONSTRAINT" in rendered
