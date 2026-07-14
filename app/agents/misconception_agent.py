"""Misconception Detection Agent — Section 11.3.
Compares the learner's claim against known concept-graph facts."""
from app.config import settings
from app.llm_client import chat, safe_json_parse

SYSTEM_PROMPT = """You are the Misconception Detection Agent. Compare the student's
latest reasoning statement against the provided canonical facts for this concept.

Respond with ONLY JSON:
{"misconception": true|false, "concept_id": "string or null", "contradiction_summary": "string or null", "confidence": 0.0-1.0}

Fail-safe rule: if you are not confident there is a contradiction, set
misconception=false. Do NOT over-flag — a false "no misconception" is safer
than a false accusation.
"""

DEFAULT = {"misconception": False, "concept_id": None, "contradiction_summary": None, "confidence": 0.0}


async def run_misconception_check(concept_name: str, canonical_facts: dict, student_message: str) -> dict:
    facts_str = "\n".join(f"- {v}" for v in canonical_facts.values()) or "(no facts on file)"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Concept: {concept_name}\nCanonical facts:\n{facts_str}\n\n"
            f"Student statement: {student_message}",
        },
    ]
    try:
        raw = await chat(messages, model=settings.LLM_MODEL_FAST, temperature=0.1, max_tokens=200, json_mode=True)
    except Exception:
        return DEFAULT

    parsed = safe_json_parse(raw, DEFAULT)
    # Fail-safe toward not over-flagging (Section 11.3)
    if parsed.get("confidence", 0) < 0.6:
        parsed["misconception"] = False
    return {**DEFAULT, **parsed}
