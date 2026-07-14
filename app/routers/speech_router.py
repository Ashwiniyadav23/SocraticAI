"""
Speech router — STT and TTS endpoints.

STT  POST /v1/speech/transcribe
     Accepts a raw audio file upload (webm/wav/mp4/ogg).
     Returns {"transcript": "<text>"}

TTS  POST /v1/speech/synthesize
     Accepts JSON body {"text": "...", "voice": "alloy"}
     Streams back raw MP3 audio bytes (Content-Type: audio/mpeg).

Architecture note
-----------------
The browser handles *recording* (via the Web Speech API or MediaRecorder) and
*playback* (via the HTMLAudioElement / Web Audio API). This Python layer
provides the server-side models: Whisper for STT and OpenAI TTS-1 for TTS.
Both use the same LLM_API_KEY / LLM_BASE_URL configured in .env so that
swapping to a different OpenAI-compatible provider requires zero code changes.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.llm_client import transcribe_audio, synthesize_speech
from app.models import User

logger = logging.getLogger("speech_router")

router = APIRouter(prefix="/v1/speech", tags=["speech"])

# ---------------------------------------------------------------------------
# Supported audio MIME types accepted by Whisper
# ---------------------------------------------------------------------------
ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/flac",
    "video/webm",   # Chrome records webm/opus under this MIME
    "application/octet-stream",  # fallback when browser sends no Content-Type
}

MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB — Whisper API limit


# ---------------------------------------------------------------------------
# STT — Speech-to-Text
# ---------------------------------------------------------------------------
@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(..., description="Audio file recorded by the browser"),
    current_user: User = Depends(get_current_user),
):
    """
    Transcribe student speech to text using Whisper.

    The browser (Web Speech API or MediaRecorder) sends a recorded audio blob
    here. The response contains the plain-text transcript which the frontend
    inserts into the chat input before calling the tutor WebSocket endpoint.

    Accepted formats: webm, wav, mp3, ogg, flac, mp4 (anything Whisper supports).
    """
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio type '{content_type}'. "
                   f"Accepted: {sorted(ALLOWED_AUDIO_TYPES)}",
        )

    audio_bytes = await file.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large ({len(audio_bytes) // 1024} KB). "
                   f"Maximum allowed: {MAX_AUDIO_BYTES // 1024 // 1024} MB.",
        )
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    # Use the original filename (or a safe default) so Whisper can infer format
    safe_filename = file.filename or f"recording.{_ext_from_mime(content_type)}"

    try:
        transcript = await transcribe_audio(audio_bytes, safe_filename)
    except Exception as exc:
        logger.error("STT error for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=502, detail=f"Speech recognition failed: {exc}") from exc

    return {"transcript": transcript.strip()}


# ---------------------------------------------------------------------------
# TTS — Text-to-Speech
# ---------------------------------------------------------------------------
_VALID_VOICES = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096, description="Text to speak")
    voice: str = Field(
        "nova",
        description="OpenAI TTS voice ID. One of: alloy, echo, fable, onyx, nova, shimmer",
    )


@router.post(
    "/synthesize",
    response_class=StreamingResponse,
    responses={200: {"content": {"audio/mpeg": {}}}},
)
async def synthesize(
    body: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Synthesize tutor text to speech using OpenAI TTS-1 (neural, low-latency).

    Returns a streaming MP3 audio response. The browser can play it directly:

        const resp = await fetch('/v1/speech/synthesize', {method:'POST', body: ...});
        const blob = await resp.blob();
        const url  = URL.createObjectURL(blob);
        new Audio(url).play();

    Voice options: alloy (neutral), echo (male), fable (british), onyx (deep),
                   nova (female, default), shimmer (warm female).
    """
    if body.voice not in _VALID_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice '{body.voice}'. Choose from: {sorted(_VALID_VOICES)}",
        )

    # Clean markdown/HTML so TTS doesn't speak "asterisk asterisk bold asterisk"
    clean_text = _clean_for_tts(body.text)
    if not clean_text.strip():
        raise HTTPException(status_code=400, detail="Text is empty after cleaning.")

    try:
        audio_bytes = await synthesize_speech(clean_text, voice=body.voice)
    except Exception as exc:
        logger.error("TTS error for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=502, detail=f"Speech synthesis failed: {exc}") from exc

    # Stream the audio back so the browser can start playing before full download
    async def _audio_stream():
        yield audio_bytes

    return StreamingResponse(
        _audio_stream(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=response.mp3"},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ext_from_mime(mime: str) -> str:
    """Map MIME type to a file extension Whisper can parse."""
    mapping = {
        "audio/webm":  "webm",
        "video/webm":  "webm",
        "audio/wav":   "wav",
        "audio/wave":  "wav",
        "audio/x-wav": "wav",
        "audio/mpeg":  "mp3",
        "audio/mp4":   "mp4",
        "audio/ogg":   "ogg",
        "audio/flac":  "flac",
    }
    return mapping.get(mime, "webm")


def _clean_for_tts(text: str) -> str:
    """
    Strip Markdown and HTML markup before passing to TTS so the model
    doesn't read punctuation artifacts aloud.
    Mirrors the `cleanTextForTTS` helper from the speech-to-speech JS library.
    """
    import re
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]*`", "", text)
    # Remove Markdown bold/italic markers
    text = re.sub(r"\*{1,3}|_{1,3}", "", text)
    # Remove Markdown links — keep link text
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
