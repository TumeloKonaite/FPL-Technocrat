from __future__ import annotations

import re
from collections.abc import Sequence


_GAMEWEEK_PATTERNS = (
    "gw{gameweek}",
    "gw {gameweek}",
    "gameweek {gameweek}",
    "game week {gameweek}",
)

_FPL_CONTEXT_KEYWORDS = (
    "fpl",
    "fantasy premier league",
    "preview",
    "deadline",
    "team selection",
    "watchlist",
    "wildcard",
    "captain",
    "captaincy",
    "transfer",
    "draft",
    "best picks",
)

_IRRELEVANT_KEYWORDS = (
    "stream highlights",
    "career mode",
    "fc 26",
    "eafc",
    "reaction",
    "vlog",
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _mentions_gameweek(text: str, gameweek: int) -> bool:
    normalized = _normalize_text(text)
    return any(
        pattern.format(gameweek=gameweek) in normalized
        for pattern in _GAMEWEEK_PATTERNS
    )


def _has_fpl_context(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(keyword in normalized for keyword in _FPL_CONTEXT_KEYWORDS)


def _looks_irrelevant(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(keyword in normalized for keyword in _IRRELEVANT_KEYWORDS)


def is_relevant_video(
    *,
    gameweek: int,
    title: str,
    transcript: str = "",
) -> bool:
    combined_text = " ".join(part for part in (title, transcript) if part).strip()
    if not combined_text:
        return False
    if _looks_irrelevant(combined_text):
        return False
    if _mentions_gameweek(combined_text, gameweek):
        return True
    return _has_fpl_context(combined_text)


def filter_relevant_videos(
    candidates: Sequence[dict[str, str]],
    *,
    gameweek: int,
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for candidate in candidates:
        title = candidate.get("title", "")
        transcript = candidate.get("transcript", "")
        if is_relevant_video(gameweek=gameweek, title=title, transcript=transcript):
            selected.append(candidate)
    return selected
