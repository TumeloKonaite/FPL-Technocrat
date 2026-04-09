from __future__ import annotations

import re
import unicodedata


PLAYER_ALIASES = {
    "saka": "bukayo saka",
    "bukayo saka": "bukayo saka",
    "haaland": "erling haaland",
    "erling haaland": "erling haaland",
    "isak": "alexander isak",
    "alexander isak": "alexander isak",
    "palmer": "cole palmer",
    "cole palmer": "cole palmer",
    "watkins": "ollie watkins",
    "ollie watkins": "ollie watkins",
    "salah": "mohamed salah",
    "mo salah": "mohamed salah",
    "mohamed salah": "mohamed salah",
    "bruno": "bruno fernandes",
    "bruno fernandes": "bruno fernandes",
}

CHIP_ALIASES = {
    "wc": "wildcard",
    "wildcard": "wildcard",
    "bb": "bench_boost",
    "bench boost": "bench_boost",
    "benchboost": "bench_boost",
    "bench_boost": "bench_boost",
    "fh": "free_hit",
    "free hit": "free_hit",
    "freehit": "free_hit",
    "free_hit": "free_hit",
    "tc": "triple_captain",
    "triple captain": "triple_captain",
    "triplecaptain": "triple_captain",
    "triple_captain": "triple_captain",
    "am": "assistant_manager",
    "assistant manager": "assistant_manager",
    "assistant_manager": "assistant_manager",
    "none": "none",
    "no chip": "none",
    "dont use chip": "none",
    "don't use chip": "none",
    "hold": "none",
}

def _basic_normalize(value: str | None) -> str:
    if value is None:
        return ""

    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9\s_-]", "", normalized)
    normalized = re.sub(r"[_-]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def normalize_lookup_key(value: str | None) -> str:
    return _basic_normalize(value)


def normalize_player_name(name: str) -> str:
    key = _basic_normalize(name)
    return PLAYER_ALIASES.get(key, key)


def normalize_chip_name(chip: str | None) -> str:
    key = _basic_normalize(chip)
    return CHIP_ALIASES.get(key, key or "none")


def normalize_text_label(text: str) -> str:
    return _basic_normalize(text)


def titleize_normalized(value: str) -> str:
    if not value:
        return ""
    return " ".join(part.capitalize() for part in value.split())


def canonical_player_display(name: str) -> str:
    return titleize_normalized(normalize_player_name(name))


def canonical_chip_display(chip: str | None) -> str:
    return normalize_chip_name(chip)
