import logging
from app.ai.model_router import chat, safe_json_parse

logger = logging.getLogger("topic_agent")

async def extract_topic(message: str) -> str:
    """
    Analyzes the student's first message to infer the learning topic.
    Returns the exact topic, or "General Inquiry" if it's casual chat.
    """
    sys_prompt = (
        "You are an intent detection agent for an AI learning platform.\n"
        "Your task is to analyze the student's message and extract the core academic or learning topic.\n"
        "If the user is just saying hello or asking casual questions, return 'General Inquiry'.\n"
        "Return JSON exactly like: {\"topic\": \"Extracted Topic\"}\n"
    )
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": message}
    ]
    
    try:
        response_text = await chat(messages, temperature=0.1, max_tokens=50, json_mode=True)
        data = safe_json_parse(response_text, {"topic": "General Inquiry"})
        topic = data.get("topic", "General Inquiry").strip()
        
        if not topic:
            topic = "General Inquiry"
            
        logger.info(f"Extracted topic: {topic} from message: '{message[:50]}...'")
        return topic
        
    except Exception as e:
        logger.error(f"Topic extraction failed: {e}")
        return "General Inquiry"
