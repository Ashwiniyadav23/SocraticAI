"""
Model-agnostic LLM client.

This does NOT hardcode a specific vendor. It speaks the standard OpenAI
chat-completions wire format, which is also implemented by most free-tier
providers (Groq, OpenRouter's free models, Together.ai, local Ollama, etc).
Swap providers by changing LLM_BASE_URL / LLM_MODEL / LLM_API_KEY in .env —
no code changes needed (PRD Section 4: "model-agnostic at the interface layer").
"""
import json
import logging

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger("llm_client")

_client = AsyncOpenAI(base_url=settings.LLM_BASE_URL, api_key=settings.LLM_API_KEY)


@retry(stop=stop_after_attempt(2), wait=wait_fixed(0.5))
async def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 500,
    json_mode: bool = False,
) -> str:
    """Single non-streaming completion. Returns the text content."""
    kwargs = {}
    if json_mode:
        # Not every free provider supports response_format; caller should
        # still defensively parse (see agents/*). We pass it best-effort.
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = await _client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:  # noqa: BLE001
        logger.warning("LLM call failed (json_mode=%s): %s", json_mode, e)
        if json_mode:
            # Some free providers reject response_format; retry once without it.
            resp = await _client.chat.completions.create(
                model=model or settings.LLM_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        raise


async def chat_stream(messages: list[dict], model: str | None = None, temperature: float = 0.4):
    """Async generator yielding text chunks — used by the WebSocket turn endpoint
    to satisfy NFR 'first token streamed within 2.5s p50' (Section 21)."""
    stream = await _client.chat.completions.create(
        model=model or settings.LLM_MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


def safe_json_parse(text: str, default: dict) -> dict:
    """Defensive JSON parsing per Section 11.1 failure handling: strip code
    fences, retry-shape, else fall back to a safe default."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except Exception:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except Exception:
                pass
        logger.warning("JSON parse failed, using default fallback: %r", text[:200])
        return default


async def transcribe_audio(audio_file_bytes: bytes, filename: str) -> str:
    """Transcribes audio file using OpenAI compatible STT API (e.g. Whisper)."""
    try:
        # Pass a tuple to file parameter representing (filename, file_bytes)
        resp = await _client.audio.transcriptions.create(
            file=(filename, audio_file_bytes),
            model="whisper-1",
        )
        return resp.text or ""
    except Exception as e:
        logger.error("STT transcription failed: %s", e)
        raise


async def synthesize_speech(text: str, voice: str = "alloy") -> bytes:
    """Synthesizes text into speech using OpenAI compatible TTS API."""
    try:
        resp = await _client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        return await resp.aread()
    except Exception as e:
        logger.error("TTS synthesis failed: %s", e)
        raise

