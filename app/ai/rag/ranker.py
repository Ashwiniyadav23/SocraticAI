from app.models import EducationalDocumentChunk

def rank_chunks(chunks: list[EducationalDocumentChunk], dna: dict | None, context: dict | None) -> list[EducationalDocumentChunk]:
    """
    Re-ranks chunks based on Learning DNA and Context.
    """
    if not chunks:
        return []
        
    scored_chunks = []
    
    # Get DNA attributes
    preferred_formats = []
    if dna:
        style = dna.get("learning_style", {})
        if style.get("visual"):
            preferred_formats.append("Diagram")
        if style.get("practical"):
            preferred_formats.append("Code")
            preferred_formats.append("Step-by-Step")
            
    # Get Context attributes
    purpose = context.get("purpose", "").lower() if context else ""
    urgency = context.get("urgency", "").lower() if context else ""
    
    for chunk in chunks:
        score = 0.0
        # Boost based on format
        if chunk.format in preferred_formats:
            score += 2.0
            
        # Boost based on context
        if "exam" in purpose and chunk.format == "Text":
            score += 1.0 # dense text for exam
        if urgency == "high" and chunk.format == "Step-by-Step":
            score += 2.0
            
        scored_chunks.append((score, chunk))
        
    # Stable sort by score descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 5
    return [c for score, c in scored_chunks][:5]
