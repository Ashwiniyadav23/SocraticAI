from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from app.agents import mastery_agent

class ReflectionState(TypedDict):
    concept_name: str
    evidence: dict
    mastery_result: dict | None


async def assess_mastery_node(state: ReflectionState) -> dict:
    result = await mastery_agent.assess_mastery(state["concept_name"], state["evidence"])
    return {"mastery_result": result}


builder = StateGraph(ReflectionState)

builder.add_node("assess_mastery", assess_mastery_node)

builder.add_edge(START, "assess_mastery")
builder.add_edge("assess_mastery", END)

reflection_graph = builder.compile()
