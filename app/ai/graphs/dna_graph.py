from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class DNAState(TypedDict):
    session_metrics: dict
    current_persona: str | None
    current_dependency: float | None
    
    # populated
    new_persona: str | None
    new_dependency: float | None

async def analyze_telemetry_node(state: DNAState) -> dict:
    metrics = state["session_metrics"]
    dependency = state["current_dependency"] or 0.5
    
    # Basic heuristic update based on telemetry
    if metrics.get("ai_dependency_signals", False):
        dependency = min(1.0, dependency + 0.1)
    else:
        dependency = max(0.0, dependency - 0.05)
        
    curiosity = metrics.get("curiosity_score", 0.5)
    persona = "curious" if curiosity > 0.7 else "passive"
    
    return {
        "new_persona": persona,
        "new_dependency": dependency
    }

builder = StateGraph(DNAState)
builder.add_node("analyze_telemetry", analyze_telemetry_node)
builder.add_edge(START, "analyze_telemetry")
builder.add_edge("analyze_telemetry", END)

dna_graph = builder.compile()
