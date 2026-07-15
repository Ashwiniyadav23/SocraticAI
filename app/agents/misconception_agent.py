"""Misconception Detection Agent — Section 11.3.
Compares the learner's claim against known concept-graph facts."""
from app.config import settings
from app.ai.model_router import chat, safe_json_parse

import time
from app.ai.prompts.service import PromptService

DEFAULT = {"misconception": False, "concept_id": None, "contradiction_summary": None, "confidence": 0.0}


async def run_misconception_check(concept_name: str, canonical_facts: dict, student_message: str) -> dict:
    facts_str = "\n".join(f"- {v}" for v in canonical_facts.values()) or "(no facts on file)"
    system_prompt, version = await PromptService.render("misconception", {})
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Concept: {concept_name}\nCanonical facts:\n{facts_str}\n\n"
            f"Student statement: {student_message}",
        },
    ]
    
    start_time = time.time()
    try:
        raw = await chat(messages, model=settings.LLM_MODEL_FAST, temperature=0.1, max_tokens=200, json_mode=True)
        latency = int((time.time() - start_time) * 1000)
        tokens = (len(str(messages)) + len(raw)) // 4
        await PromptService.log_evaluation("misconception", version, tokens, 0.0, latency, True)
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        await PromptService.log_evaluation("misconception", version, 0, 0.0, latency, False, str(e))
        return DEFAULT

    parsed = safe_json_parse(raw, DEFAULT)
    # Fail-safe toward not over-flagging (Section 11.3)
    if parsed.get("confidence", 0) < 0.6:
        parsed["misconception"] = False
    return {**DEFAULT, **parsed}
