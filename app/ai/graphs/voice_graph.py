from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from app.ai.model_router import transcribe_audio, synthesize_speech

class VoiceState(TypedDict):
    # Input for STT
    audio_bytes: bytes | None
    filename: str | None
    
    # Input for TTS
    text: str | None
    voice: str | None
    
    # Outputs
    transcript: str | None
    synthesized_audio: bytes | None

async def transcribe_node(state: VoiceState) -> dict:
    transcript = await transcribe_audio(state["audio_bytes"], state["filename"])
    return {"transcript": transcript.strip()}

async def synthesize_node(state: VoiceState) -> dict:
    audio_bytes = await synthesize_speech(state["text"], voice=state["voice"])
    return {"synthesized_audio": audio_bytes}


def _route_entry(state: VoiceState) -> str:
    """Route to the correct node based on whether this is an STT or TTS request."""
    if state.get("audio_bytes"):
        return "transcribe"
    return "synthesize"


builder = StateGraph(VoiceState)

builder.add_node("transcribe", transcribe_node)
builder.add_node("synthesize", synthesize_node)

builder.add_conditional_edges(START, _route_entry, {"transcribe": "transcribe", "synthesize": "synthesize"})
builder.add_edge("transcribe", END)
builder.add_edge("synthesize", END)

voice_graph = builder.compile()
