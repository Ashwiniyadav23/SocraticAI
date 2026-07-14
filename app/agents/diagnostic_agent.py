"""Diagnostic Agent — Section 11.1. Classifies understanding level + confidence."""
from app.config import settings
from app.llm_client import chat, safe_json_parse

SYSTEM_PROMPT = """You are the Diagnostic Agent inside a Socratic tutoring system.
Your ONLY job is to classify the student's current understanding level from their
latest message and recent conversation. You NEVER answer their question or teach.

Respond with ONLY a JSON object, no prose, no markdown fences:
{"level": "beginner|intermediate|advanced", "confidence": 0.0-1.0, "misconception_candidate": true|false, "correct_baseline": true|false}

- "correct_baseline": true only if the student correctly answered a basic
  calibration question about the problem (what it gives/asks, not the solution).
- Be conservative: if unsure, level="intermediate", confidence=0.5.
"""

DEFAULT = {"level": "intermediate", "confidence": 0.5, "misconception_candidate": False, "correct_baseline": False}


async def run_diagnostic(concept_name: str, recent_turns: list[dict], student_message: str) -> dict:
    history_str = "\n".join(f"{t['role']}: {t['content']}" for t in recent_turns[-6:])
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Concept: {concept_name}\n\nRecent conversation:\n{history_str}\n\n"
            f"Latest student message: {student_message}",
        },
    ]
    try:
        raw = await chat(messages, model=settings.LLM_MODEL_FAST, temperature=0.1, max_tokens=150, json_mode=True)
    except Exception:
        # Section 11.1 failure handling: default to intermediate/0.5, flag for review
        return {**DEFAULT, "_flagged_for_review": True}

    parsed = safe_json_parse(raw, DEFAULT)
    parsed.setdefault("level", DEFAULT["level"])
    parsed.setdefault("confidence", DEFAULT["confidence"])
    parsed.setdefault("misconception_candidate", False)
    parsed.setdefault("correct_baseline", False)
    return parsed
