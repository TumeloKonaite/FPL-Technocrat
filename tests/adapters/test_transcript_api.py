from __future__ import annotations

import pytest

from src.adapters.transcript_api import TranscriptFetchError, fetch_transcript


class _FakeSnippet:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeTranscript:
    def __init__(self, snippets: list[_FakeSnippet]) -> None:
        self.snippets = snippets


class _SuccessfulTranscriptApi:
    def fetch(self, video_id: str) -> _FakeTranscript:
        assert video_id == "abc123"
        return _FakeTranscript([
            _FakeSnippet(" Hello   world "),
            _FakeSnippet("gameweek\n32"),
        ])


class _BrokenTranscriptApi:
    def fetch(self, video_id: str) -> _FakeTranscript:
        raise RuntimeError(f"provider down for {video_id}")


def test_fetch_transcript_returns_combined_text(monkeypatch) -> None:
    monkeypatch.setattr(
        "youtube_transcript_api.YouTubeTranscriptApi",
        lambda: _SuccessfulTranscriptApi(),
    )

    transcript = fetch_transcript("abc123")

    assert transcript == "Hello world gameweek 32"


def test_fetch_transcript_wraps_provider_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        "youtube_transcript_api.YouTubeTranscriptApi",
        lambda: _BrokenTranscriptApi(),
    )

    with pytest.raises(TranscriptFetchError, match="Could not fetch transcript for video 'broken456'"):
        fetch_transcript("broken456")
