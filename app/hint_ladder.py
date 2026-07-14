"""Hint Escalation Ladder — Section 10. Never skips tiers."""

TIERS = {
    0: "Ask a clarifying question: what have you tried so far?",
    1: "Point to the relevant concept by name — no explanation.",
    2: "Ask a narrower guiding question about that concept.",
    3: "Give a partial structural hint (name the pattern, ask what it implies).",
    4: "Offer a worked micro-example on an ANALOGOUS problem, not this one.",
    5: "Give an explicit explanation of the concept — never the specific solution.",
}

MAX_TIER = 5


def next_tier(current_tier: int, unresolved: bool) -> int:
    if not unresolved:
        return max(0, current_tier - 1) if current_tier > 0 else 0
    return min(MAX_TIER, current_tier + 1)


def tier_instruction(tier: int) -> str:
    return TIERS.get(min(tier, MAX_TIER), TIERS[MAX_TIER])
