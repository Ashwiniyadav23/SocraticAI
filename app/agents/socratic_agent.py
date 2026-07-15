"""Socratic Questioning Agent — Section 11.2, with per-mode prompts (Section 9)."""
from app.config import settings
from app.ai.model_router import chat

from app.ai.prompts.socratic_prompts import MODE_PROMPTS


def _mode_prompt(mode: str) -> str:
    return MODE_PROMPTS.get(mode, MODE_PROMPTS["SOCRATIC_COACH"])


async def generate_response(
    mode: str,
    concept_name: str,
    recent_turns: list[dict],
    student_message: str,
    hint_tier_instruction: str,
    corrective: str | None = None,
) -> str:
    system = (
        f"You are a Socratic learning companion helping a student understand: {concept_name}.\n"
        f"{_mode_prompt(mode)}\n"
        f"Current hint tier guidance: {hint_tier_instruction}"
    )
    if corrective:
        system += f"\n\nCORRECTION NEEDED: {corrective}"

    history = [{"role": "user" if t["role"] == "student" else "assistant", "content": t["content"]}
               for t in recent_turns[-8:]]

    messages = [{"role": "system", "content": system}, *history,
                {"role": "user", "content": student_message}]

    return await chat(messages, model=settings.LLM_MODEL, temperature=0.6, max_tokens=300)
