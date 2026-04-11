from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.video_job import VideoAnalysisJob


PLAYER_ALIASES = {
    "saka": "bukayo saka",
    "bukayo saka": "bukayo saka",
    "bukayo": "bukayo saka",
    "haaland": "erling haaland",
    "erling haaland": "erling haaland",
    "erling": "erling haaland",
    "isak": "alexander isak",
    "alexander isak": "alexander isak",
    "palmer": "cole palmer",
    "cole palmer": "cole palmer",
    "cole": "cole palmer",
    "watkins": "ollie watkins",
    "ollie watkins": "ollie watkins",
    "salah": "mohamed salah",
    "m salah": "mohamed salah",
    "mo salah": "mohamed salah",
    "mohamed salah": "mohamed salah",
    "mohamed salahs": "mohamed salah",
    "bruno": "bruno fernandes",
    "bruno f": "bruno fernandes",
    "bruno fernandes": "bruno fernandes",
    "bowen": "jarrod bowen",
    "jarrod bowen": "jarrod bowen",
    "semenyo": "antoine semenyo",
    "antoine semenyo": "antoine semenyo",
    "gordon": "anthony gordon",
    "anthony gordon": "anthony gordon",
    "ampadu": "ethan ampadu",
    "ethan ampadu": "ethan ampadu",
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

_TRANSCRIPT_NOISE_PATTERN = re.compile(r"\[(?:music|applause|laughter|__+)\]|\((?:music|applause|laughter|__+)\)")
_NON_ALNUM_SPACING_PATTERN = re.compile(r"[^a-z0-9\s_-]")
_POSSESSIVE_PATTERN = re.compile(r"\b([a-z]+)'s\b")
_URL_VIDEO_ID_PATTERN = re.compile(r"(?:v=|/)([A-Za-z0-9_-]{6,})")


@dataclass(frozen=True, slots=True)
class NormalizedName:
    raw_name: str
    normalized_name: str

def _basic_normalize(value: str | None) -> str:
    if value is None:
        return ""

    normalized = str(value).replace("’", "'").replace("`", "'").replace("“", '"').replace("”", '"')
    normalized = _TRANSCRIPT_NOISE_PATTERN.sub(" ", normalized)
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = _POSSESSIVE_PATTERN.sub(r"\1", normalized)
    normalized = normalized.replace("&", " and ")
    normalized = _NON_ALNUM_SPACING_PATTERN.sub(" ", normalized)
    normalized = re.sub(r"[_-]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def normalize_lookup_key(value: str | None) -> str:
    return _basic_normalize(value)


def normalize_player_reference(name: str | None) -> NormalizedName:
    raw_name = "" if name is None else str(name)
    key = _basic_normalize(raw_name)
    return NormalizedName(raw_name=raw_name, normalized_name=PLAYER_ALIASES.get(key, key))


def normalize_player_name(name: str) -> str:
    return normalize_player_reference(name).normalized_name


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


def canonicalize_video_url(video_url: str | None) -> str:
    key = normalize_lookup_key(video_url)
    if not key:
        return ""

    match = _URL_VIDEO_ID_PATTERN.search(str(video_url))
    if match:
        return match.group(1).lower()

    return key.rstrip("/")


def fingerprint_text(value: str | None) -> str:
    normalized = normalize_lookup_key(value)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def build_video_job_identity(job: VideoAnalysisJob) -> tuple[str, str]:
    canonical_url = canonicalize_video_url(job.video_url)
    if canonical_url:
        return (f"video:{canonical_url}", "video_url")

    transcript_hash = fingerprint_text(job.transcript)
    expert_key = normalize_lookup_key(job.expert_name)
    if transcript_hash:
        return (f"transcript:{expert_key}:{transcript_hash}", "transcript")

    title_key = normalize_lookup_key(job.video_title)
    fallback_key = f"metadata:{expert_key}:{title_key}:{job.gameweek}"
    return (fallback_key, "metadata")


def build_analysis_identity(analysis: ExpertVideoAnalysis) -> tuple[str, str]:
    def _normalized_players(players: list[str]) -> str:
        return ",".join(
            sorted(
                normalized
                for player in players
                if (normalized := normalize_player_name(player))
            )
        )

    def _normalized_text(items: list[str]) -> str:
        return ",".join(
            sorted(
                normalized
                for item in items
                if (normalized := normalize_text_label(item))
            )
        )

    payload = "|".join(
        [
            normalize_lookup_key(analysis.expert_name),
            normalize_lookup_key(analysis.video_title),
            normalize_lookup_key(analysis.summary),
            _normalized_players(analysis.recommended_players),
            _normalized_players(analysis.avoid_players),
            _normalized_players(analysis.captaincy_picks),
            _normalized_players(analysis.current_team),
            _normalized_players(analysis.starting_xi),
            _normalized_players(analysis.bench),
            _normalized_players(analysis.transfers_in),
            _normalized_players(analysis.transfers_out),
            normalize_player_name(analysis.captain),
            normalize_player_name(analysis.vice_captain),
            normalize_chip_name(analysis.chip_strategy),
            _normalized_text(analysis.key_takeaways),
            _normalized_text(analysis.reasoning),
        ]
    )
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return (f"analysis:{normalize_lookup_key(analysis.expert_name)}:{payload_hash}", "analysis_content")
