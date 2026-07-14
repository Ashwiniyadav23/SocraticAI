"""Answer-Leak Guard — Section 11.6. The single highest-leverage safety
component in the system. Two layers: deterministic rules, then a cheap
LLM classifier for subtler leaks."""
import re

from app.config import settings
from app.llm_client import chat, safe_json_parse

# Deterministic rule 1: a complete, runnable-looking code block is a strong
# leak signal for coding problems (full function body, not a skeleton/blank).
_CODE_BLOCK_RE = re.compile(r"```[\w]*\n(.*?)```", re.DOTALL)
_BLANK_MARKERS = ("____", "# TODO", "...", "<blank>", "# your code here")


def _rule_based_leak(text: str) -> bool:
    for block in _CODE_BLOCK_RE.findall(text):
        stripped = block.strip()
        if not stripped:
            continue
        has_blank = any(marker in stripped for marker in _BLANK_MARKERS)
        looks_complete = ("return" in stripped or "print(" in stripped) and len(stripped.splitlines()) >= 3
        if looks_complete and not has_blank:
            return True
    # "the answer is X" / "the final answer is" patterns
    lowered = text.lower()
    direct_answer_phrases = ["the answer is", "the solution is", "final answer:", "just do this:"]
    if any(p in lowered for p in direct_answer_phrases):
        return True
    return False


SYSTEM_PROMPT = """You check whether a tutor's message accidentally reveals the
direct solution to the student's problem instead of asking a guiding question.
Respond with ONLY JSON: {"leak": true|false, "reason": "short string"}
A message that asks a question, gives a hint, or provides a SKELETON with
blanks is NOT a leak. A message that states the final approach/code/answer
outright IS a leak.
"""


async def check_leak(tutor_message: str) -> tuple[bool, str]:
    if _rule_based_leak(tutor_message):
        return True, "rule_based: complete code block or direct-answer phrase detected"

    try:
        raw = await chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": tutor_message},
            ],
            model=settings.LLM_MODEL_FAST,
            temperature=0.0,
            max_tokens=100,
            json_mode=True,
        )
    except Exception:
        # Fail closed on the side of NOT blocking indefinitely — but log for review.
        return False, "classifier_unavailable"

    parsed = safe_json_parse(raw, {"leak": False, "reason": "parse_failed"})
    return bool(parsed.get("leak", False)), parsed.get("reason", "")
