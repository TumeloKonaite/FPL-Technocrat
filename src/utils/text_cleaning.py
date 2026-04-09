"""
Helpers for normalizing transcript text.
"""

import re


def clean_transcript(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()
