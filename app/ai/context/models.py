from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LearningContext(BaseModel):
    purpose: str = Field(description="The 'why' behind the learning session (e.g. Interview Prep, Exam, Curiosity, General Learning)")
    urgency: str = Field(description="Urgency of the learning: High, Medium, or Low")
    deadline: Optional[str] = Field(None, description="ISO format deadline if applicable")
    expected_depth: str = Field(description="Expected depth: Surface, Functional, Deep, Mastery")
    objective: str = Field(description="The specific skill or knowledge target")
