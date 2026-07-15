from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class MentorState(TypedDict):
    student_id: str
    analytics_data: dict
    
    # populated
    at_risk: bool
    intervention_plan: str | None

async def analyze_risk_node(state: MentorState) -> dict:
    data = state["analytics_data"]
    at_risk = False
    intervention = None
    
    # Mock risk analysis logic
    if data.get("recent_failures", 0) > 3 or data.get("dependency_score", 0.0) > 0.8:
        at_risk = True
        intervention = "Suggest a 1-on-1 mentor session to review core concepts."
        
    return {"at_risk": at_risk, "intervention_plan": intervention}


builder = StateGraph(MentorState)
builder.add_node("analyze_risk", analyze_risk_node)
builder.add_edge(START, "analyze_risk")
builder.add_edge("analyze_risk", END)

mentor_graph = builder.compile()
