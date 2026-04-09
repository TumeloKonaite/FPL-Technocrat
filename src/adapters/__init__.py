"""Adapter interfaces for transcript ingestion and persistence."""

from src.adapters.storage import load_transcript, save_transcript
from src.adapters.transcript_api import fetch_transcript
from src.adapters.youtube import fetch_youtube_transcript

__all__ = [
    "fetch_transcript",
    "fetch_youtube_transcript",
    "load_transcript",
    "save_transcript",
]
