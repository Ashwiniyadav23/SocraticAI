"""Socratic Questioning Agent — Section 11.2, with per-mode prompts (Section 9)."""
from app.config import settings
from app.ai.model_router import chat

import time
from app.ai.prompts.service import PromptService


async def generate_response(
    mode: str,
    concept_name: str,
    recent_turns: list[dict],
    student_message: str,
    hint_tier_instruction: str,
    retrieved_context: list[dict] | None = None,
    corrective: str | None = None,
) -> str:
    mode_prompt, version = await PromptService.render("socratic_tutor", {"tutor_mode": mode})
    system = (
        f"You are a Socratic learning companion helping a student understand: {concept_name}.\n"
        f"{mode_prompt}\n"
        f"Current hint tier guidance: {hint_tier_instruction}"
    )
    
    if retrieved_context:
        context_str = "\n\n".join(
            f"[Source Format: {c.get('format', 'Text')}]\n{c.get('text', '')}"
            for c in retrieved_context
        )
        system += (
            f"\n\nEDUCATIONAL CONTEXT:\n{context_str}\n\n"
            "INSTRUCTION: Answer ONLY using the provided educational context above. "
            "You MUST output inline citations like [Source: Format] if you use the context."
        )

    if corrective:
        system += f"\n\nCORRECTION NEEDED: {corrective}"

    history = [{"role": "user" if t["role"] == "student" else "assistant", "content": t["content"]}
               for t in recent_turns[-8:]]

    messages = [{"role": "system", "content": system}, *history,
                {"role": "user", "content": student_message}]

    start_time = time.time()
    try:
        res = await chat(messages, model=settings.LLM_MODEL, temperature=0.6, max_tokens=300)
        latency = int((time.time() - start_time) * 1000)
        tokens = (len(str(messages)) + len(res)) // 4
        await PromptService.log_evaluation("socratic_tutor", version, tokens, 0.0, latency, True)
        return res
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        await PromptService.log_evaluation("socratic_tutor", version, 0, 0.0, latency, False, str(e))
        raise
