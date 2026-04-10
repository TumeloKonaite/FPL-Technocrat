from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


def _parse_bool(value: str | None) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class WebshareProxySettings:
    enabled: bool = False
    proxy_username: str | None = None
    proxy_password: str | None = None


class TranscriptApiConfigError(ValueError):
    """Raised when transcript API configuration is invalid."""


class TranscriptFetchError(RuntimeError):
    """Raised when transcript retrieval fails."""


def load_webshare_proxy_settings(
    env: Mapping[str, str] | None = None,
) -> WebshareProxySettings:
    environment = env or os.environ
    return WebshareProxySettings(
        enabled=_parse_bool(environment.get("ENABLE_WEBSHARE_PROXY")),
        proxy_username=environment.get("WEBSHARE_PROXY_USERNAME"),
        proxy_password=environment.get("WEBSHARE_PROXY_PASSWORD"),
    )


def _build_transcript_api(
    proxy_settings: WebshareProxySettings | None = None,
):
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.proxies import WebshareProxyConfig

    settings = proxy_settings or WebshareProxySettings()
    if not settings.enabled:
        return YouTubeTranscriptApi()

    if not settings.proxy_username or not settings.proxy_password:
        raise TranscriptApiConfigError(
            "Webshare proxy is enabled but WEBSHARE_PROXY_USERNAME or "
            "WEBSHARE_PROXY_PASSWORD is missing."
        )

    return YouTubeTranscriptApi(
        proxy_config=WebshareProxyConfig(
            proxy_username=settings.proxy_username,
            proxy_password=settings.proxy_password,
        )
    )


def fetch_transcript(
    video_id: str,
    proxy_settings: WebshareProxySettings | None = None,
) -> str:
    """Fetch a raw transcript string from the configured transcript source."""
    try:
        transcript = _build_transcript_api(proxy_settings).fetch(video_id)
        combined_transcript = " ".join(
            " ".join(snippet.text.split())
            for snippet in transcript.snippets
        )
        return combined_transcript.strip()
    except TranscriptApiConfigError:
        raise
    except Exception as exc:
        raise TranscriptFetchError(
            f"Could not fetch transcript for video '{video_id}': {exc}"
        ) from exc
