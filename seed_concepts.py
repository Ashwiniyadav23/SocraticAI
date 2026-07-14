"""Manual seed script: populates a few DSA concepts with canonical facts used
by the Misconception Detection Agent (Section 12, Concept Graph).

Run manually after the DB is up:
    python scripts_seed_concepts.py
"""
import asyncio

from app.database import AsyncSessionLocal, init_db
from app.models import Concept

SEED = [
    {
        "name": "Two Sum / Hash Maps",
        "domain": "dsa",
        "prerequisites": [],
        "canonical_facts": {
            "f1": "A hash map gives average O(1) lookup time, not O(log n).",
            "f2": "Brute-force checking every pair for Two Sum is O(n^2) time.",
            "f3": "Using a hash map, Two Sum can be solved in O(n) time and O(n) space.",
        },
    },
    {
        "name": "Binary Search",
        "domain": "dsa",
        "prerequisites": [],
        "canonical_facts": {
            "f1": "Binary search requires the input to be sorted.",
            "f2": "Binary search runs in O(log n) time.",
            "f3": "Binary search halves the search space each iteration.",
        },
    },
]


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        for item in SEED:
            db.add(Concept(**item))
        await db.commit()
    print(f"Seeded {len(SEED)} concepts.")


if __name__ == "__main__":
    asyncio.run(main())
