"""Speech-to-text with Whisper and behavioral analytics."""
from __future__ import annotations

import os
import tempfile
from typing import Any

import whisper

_model = None


def load_whisper_model(model_name: str = "base") -> whisper.Whisper:
    global _model
    if _model is None:
        _model = whisper.load_model(model_name)
    return _model


def transcribe_audio(audio_bytes: bytes, model_name: str = "base") -> dict[str, Any]:
    model = load_whisper_model(model_name)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        path = tmp.name
    try:
        result = model.transcribe(path)
        return {
            "text": result["text"],
            "language": result.get("language"),
            "segments": result.get("segments", []),
        }
    finally:
        os.remove(path)
