"""Mastery Assessment Agent — Section 11.4 + Section 14 weighted rubric."""
from app.config import settings
from app.ai.model_router import chat, safe_json_parse

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

import time
from app.ai.prompts.service import PromptService

DEFAULT = {k: 0 for k in WEIGHTS} | {"weak_areas": []}


async def assess_mastery(concept_name: str, evidence: dict) -> dict:
    """`evidence` is a dict of raw student artifacts, e.g.
    {"teach_back_text": "...", "transfer_task_attempt": "...", ...}
    Missing keys are treated as no evidence for that component."""
    evidence_str = "\n".join(f"{k}: {v}" for k, v in evidence.items() if v) or "(no evidence submitted)"

    system_prompt, version = await PromptService.render("mastery", {})
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Concept: {concept_name}\n\nEvidence:\n{evidence_str}"},
    ]

    start_time = time.time()
    try:
        raw = await chat(messages, model=settings.LLM_MODEL, temperature=0.2, max_tokens=400, json_mode=True)
        latency = int((time.time() - start_time) * 1000)
        tokens = (len(str(messages)) + len(raw)) // 4
        await PromptService.log_evaluation("mastery", version, tokens, 0.0, latency, True)
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        await PromptService.log_evaluation("mastery", version, 0, 0.0, latency, False, str(e))
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
