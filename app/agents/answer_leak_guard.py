"""Answer-Leak Guard — Section 11.6. The single highest-leverage safety
component in the system. Two layers: deterministic rules, then a cheap
LLM classifier for subtler leaks."""
import re

from app.config import settings
from app.ai.model_router import chat, safe_json_parse

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


import time
from app.ai.prompts.service import PromptService


async def check_leak(tutor_message: str) -> tuple[bool, str]:
    if _rule_based_leak(tutor_message):
        return True, "rule_based: complete code block or direct-answer phrase detected"

    start_time = time.time()
    try:
        system_prompt, version = await PromptService.render("leak_guard", {})
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": tutor_message},
        ]
        raw = await chat(
            messages,
            model=settings.LLM_MODEL_FAST,
            temperature=0.0,
            max_tokens=100,
            json_mode=True,
        )
        latency = int((time.time() - start_time) * 1000)
        tokens = (len(str(messages)) + len(raw)) // 4
        await PromptService.log_evaluation("leak_guard", version, tokens, 0.0, latency, True)
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        # Attempt to extract version if it failed after render, else fallback
        version_str = locals().get("version", "unknown")
        await PromptService.log_evaluation("leak_guard", version_str, 0, 0.0, latency, False, str(e))
        # Fail closed on the side of NOT blocking indefinitely — but log for review.
        return False, "classifier_unavailable"

    parsed = safe_json_parse(raw, {"leak": False, "reason": "parse_failed"})
    return bool(parsed.get("leak", False)), parsed.get("reason", "")
