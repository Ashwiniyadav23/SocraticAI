"""Diagnostic Agent — Section 11.1. Classifies understanding level + confidence."""
from app.config import settings
from app.ai.model_router import chat, safe_json_parse

import time
from app.ai.prompts.service import PromptService

DEFAULT = {"level": "intermediate", "confidence": 0.5, "misconception_candidate": False, "correct_baseline": False, "shared_ai_usage": False}


async def run_diagnostic(concept_name: str, recent_turns: list[dict], student_message: str) -> dict:
    history_str = "\n".join(f"{t['role']}: {t['content']}" for t in recent_turns[-6:])
    system_prompt, version = await PromptService.render("diagnostic", {})
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Concept: {concept_name}\n\nRecent conversation:\n{history_str}\n\n"
            f"Latest student message: {student_message}",
        },
    ]
    
    start_time = time.time()
    try:
        raw = await chat(messages, model=settings.LLM_MODEL_FAST, temperature=0.1, max_tokens=150, json_mode=True)
        latency = int((time.time() - start_time) * 1000)
        tokens = (len(str(messages)) + len(raw)) // 4
        await PromptService.log_evaluation("diagnostic", version, tokens, 0.0, latency, True)
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        await PromptService.log_evaluation("diagnostic", version, 0, 0.0, latency, False, str(e))
        # Section 11.1 failure handling: default to intermediate/0.5, flag for review
        return {**DEFAULT, "_flagged_for_review": True}

    parsed = safe_json_parse(raw, DEFAULT)
    parsed.setdefault("level", DEFAULT["level"])
    parsed.setdefault("confidence", DEFAULT["confidence"])
    parsed.setdefault("misconception_candidate", False)
    parsed.setdefault("correct_baseline", False)
    parsed.setdefault("shared_ai_usage", False)
    return parsed
