from app.ai.model_router import chat
from app.config import settings

async def rewrite_query(student_message: str, weak_topics: list[str], recent_turns: list[dict]) -> str:
    """
    Rewrites the user's query incorporating weak spots and context.
    """
    system = (
        "You are a query rewriting assistant for a vector search engine.\n"
        "Given the student's message and their known weak topics, rewrite the query to maximize semantic retrieval.\n"
        "Include relevant keywords from the weak topics if they apply to the student's message.\n"
        "Output ONLY the rewritten search query, nothing else."
    )
    
    user_msg = f"Weak Topics: {', '.join(weak_topics) if weak_topics else 'None'}\nStudent Message: {student_message}"
    
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg}
    ]
    
    try:
        res = await chat(messages, model=settings.LLM_MODEL_FAST, temperature=0.2, max_tokens=100)
        return res.strip()
    except Exception:
        return student_message
