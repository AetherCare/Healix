"""
Whisper API transcription gateway via Groq-hosted Whisper models.
"""

import io
import logging
from typing import Optional, Tuple

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def transcribe_audio(content: bytes, filename: str) -> Tuple[str, Optional[str]]:
    """
    Transcribe audio bytes using Groq Whisper API.

    Args:
        content: Raw audio file bytes.
        filename: Original filename for MIME hinting.

    Returns:
        Tuple of (transcript, detected_language).
    """
    settings = get_settings()
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY not configured; returning placeholder transcript")
        return "[Transcription unavailable — configure GROQ_API_KEY]", None

    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.groq_api_key)
        audio_file = io.BytesIO(content)
        audio_file.name = filename

        response = await client.audio.transcriptions.create(
            file=(filename, audio_file),
            model=settings.whisper_model,
            response_format="verbose_json",
        )
        transcript = response.text if hasattr(response, "text") else str(response)
        language = getattr(response, "language", None)
        return transcript, language
    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
        raise
