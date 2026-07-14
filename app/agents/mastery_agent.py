"""Mastery Assessment Agent — Section 11.4 + Section 14 weighted rubric."""
from app.config import settings
from app.llm_client import chat, safe_json_parse

WEIGHTS = {
    "teach_back": 0.20,
    "transfer_task": 0.30,
    "problem_variation": 0.15,
    "tracing": 0.15,
    "prediction": 0.10,
    "reasoning_quality": 0.10,
}

MASTERY_THRESHOLD = 75
MIN_COMPONENT_FLOOR = 50  # prevents "high average, one big gap" false mastery

SYSTEM_PROMPT = """You are the Mastery Assessment Agent. Score the student's evidence
against a rubric with 6 components, each 0-100. Be strict: a component with no
evidence provided should score 0, not be omitted.

Respond with ONLY JSON:
{"teach_back": 0-100, "transfer_task": 0-100, "problem_variation": 0-100,
 "tracing": 0-100, "prediction": 0-100, "reasoning_quality": 0-100,
 "weak_areas": ["..."]}
"""

DEFAULT = {k: 0 for k in WEIGHTS} | {"weak_areas": []}


async def assess_mastery(concept_name: str, evidence: dict) -> dict:
    """`evidence` is a dict of raw student artifacts, e.g.
    {"teach_back_text": "...", "transfer_task_attempt": "...", ...}
    Missing keys are treated as no evidence for that component."""
    evidence_str = "\n".join(f"{k}: {v}" for k, v in evidence.items() if v) or "(no evidence submitted)"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Concept: {concept_name}\n\nEvidence:\n{evidence_str}"},
    ]

    try:
        raw = await chat(messages, model=settings.LLM_MODEL, temperature=0.2, max_tokens=400, json_mode=True)
    except Exception:
        return {"mastery_score": 0.0, "evidence_breakdown": DEFAULT, "eligible_for_mastered": False,
                "reason": "assessment_failed_insufficient_evidence"}

    parsed = safe_json_parse(raw, DEFAULT)
    breakdown = {k: float(parsed.get(k, 0)) for k in WEIGHTS}
    score = sum(breakdown[k] * w for k, w in WEIGHTS.items())

    eligible = score >= MASTERY_THRESHOLD and all(v >= MIN_COMPONENT_FLOOR for v in breakdown.values())
    # FR-04: mastery cannot be marked without transfer-task evidence
    if not evidence.get("transfer_task_attempt"):
        eligible = False

    return {
        "mastery_score": round(score, 1),
        "evidence_breakdown": breakdown,
        "weak_areas": parsed.get("weak_areas", []),
        "eligible_for_mastered": eligible,
    }
