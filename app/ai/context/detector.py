from app.ai.model_router import chat, safe_json_parse
from app.config import settings
from app.ai.context.models import LearningContext

async def detect_context(student_message: str, recent_turns: list) -> LearningContext:
    """
    Analyzes the initial prompts and session metadata to classify the purpose and urgency.
    """
    system_prompt = (
        "You are the Learning Context Engine. Your job is to determine the 'WHY' behind a student's learning session.\n"
        "Analyze the student's message and recent conversation to extract the purpose, urgency, expected depth, and objective.\n"
        "Valid purposes: Interview Prep, Assignment, Exam, Project, Curiosity, Career Growth, Communication, General Learning.\n"
        "Valid urgencies: Low, Medium, High.\n"
        "Valid expected depths: Surface, Functional, Deep, Mastery.\n"
        "Output ONLY JSON matching this schema:\n"
        "{\n"
        '  "purpose": "...",\n'
        '  "urgency": "...",\n'
        '  "deadline": "ISO-8601 string or null",\n'
        '  "expected_depth": "...",\n'
        '  "objective": "..."\n'
        "}"
    )
    
    context_str = f"Student Message: {student_message}\nRecent Turns: {recent_turns}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context_str}
    ]
    
    try:
        raw_response = await chat(messages, model=settings.LLM_MODEL_FAST, temperature=0.1, max_tokens=150, json_mode=True)
        parsed = safe_json_parse(raw_response, {})
        
        return LearningContext(
            purpose=parsed.get("purpose", "General Learning"),
            urgency=parsed.get("urgency", "Low"),
            deadline=parsed.get("deadline"),
            expected_depth=parsed.get("expected_depth", "Functional"),
            objective=parsed.get("objective", "Understand the concept")
        )
    except Exception as e:
        print(f"LCES Detection Error: {e}")
        # Fallback context
        return LearningContext(
            purpose="General Learning",
            urgency="Low",
            deadline=None,
            expected_depth="Functional",
            objective="General understanding"
        )
