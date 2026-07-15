"""Cheap, non-LLM confidence/overload heuristics — Section 8.
Kept out of the LLM entirely for cost control (Section 11.5 orchestration budget)."""
import re

HEDGE_WORDS = ["maybe", "i think", "not sure", "i guess", "probably", "kind of", "sort of"]
STUCK_PHRASES = ["i don't know", "idk", "no idea", "just tell me", "give me the answer",
                  "give me the code", "just give me", "skip this", "i give up"]


def hedge_word_frequency(text: str) -> float:
    lowered = text.lower()
    count = sum(lowered.count(w) for w in HEDGE_WORDS)
    words = max(1, len(text.split()))
    return min(1.0, count / max(1, words / 15))


def is_stuck_signal(text: str) -> bool:
    lowered = text.lower().strip()
    if not lowered:
        return True
    return any(p in lowered for p in STUCK_PHRASES) or len(lowered.split()) <= 2


def overload_flag(text: str, prior_len_avg: float, skip_count: int) -> bool:
    sudden_short = len(text.split()) < max(3, prior_len_avg * 0.3) if prior_len_avg else False
    hedge_spike = hedge_word_frequency(text) > 0.5
    wants_skip = "skip" in text.lower()
    return sudden_short or hedge_spike or (wants_skip and skip_count >= 1)


def curiosity_score(text: str) -> float:
    lowered = text.lower()
    markers = ["why", "what if", "how come", "what happens if", "curious"]
    hits = sum(lowered.count(m) for m in markers)
    return min(1.0, hits / 2)


def aggregate_confidence(self_rated: float, hedge_freq: float, recent_correct_ratio: float) -> float:
    """Weighted blend per Section 8: self-report + hedge language + recent correctness."""
    return round(max(0.0, min(1.0, 0.4 * self_rated + 0.3 * (1 - hedge_freq) + 0.3 * recent_correct_ratio)), 2)
