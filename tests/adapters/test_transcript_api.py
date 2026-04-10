from __future__ import annotations

import pytest

from src.adapters.transcript_api import (
    TranscriptApiConfigError,
    TranscriptFetchError,
    WebshareProxySettings,
    fetch_transcript,
    load_webshare_proxy_settings,
)


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


class _RecordingTranscriptApi:
    def __init__(self, proxy_config=None) -> None:
        self.proxy_config = proxy_config

    def fetch(self, video_id: str) -> _FakeTranscript:
        assert video_id == "abc123"
        return _FakeTranscript([_FakeSnippet(" proxied transcript ")])


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


def test_load_webshare_proxy_settings_reads_environment_values() -> None:
    settings = load_webshare_proxy_settings(
        {
            "ENABLE_WEBSHARE_PROXY": "true",
            "WEBSHARE_PROXY_USERNAME": "proxy-user",
            "WEBSHARE_PROXY_PASSWORD": "proxy-pass",
        }
    )

    assert settings == WebshareProxySettings(
        enabled=True,
        proxy_username="proxy-user",
        proxy_password="proxy-pass",
    )


def test_fetch_transcript_initializes_plain_client_when_proxy_disabled(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_client(proxy_config=None):
        captured["proxy_config"] = proxy_config
        return _RecordingTranscriptApi(proxy_config=proxy_config)

    monkeypatch.setattr("youtube_transcript_api.YouTubeTranscriptApi", _fake_client)

    transcript = fetch_transcript(
        "abc123",
        proxy_settings=WebshareProxySettings(enabled=False),
    )

    assert transcript == "proxied transcript"
    assert captured == {"proxy_config": None}


def test_fetch_transcript_initializes_webshare_client_when_proxy_enabled(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _FakeWebshareProxyConfig:
        def __init__(self, proxy_username: str, proxy_password: str) -> None:
            self.proxy_username = proxy_username
            self.proxy_password = proxy_password

    def _fake_client(proxy_config=None):
        captured["proxy_config"] = proxy_config
        return _RecordingTranscriptApi(proxy_config=proxy_config)

    monkeypatch.setattr("youtube_transcript_api.YouTubeTranscriptApi", _fake_client)
    monkeypatch.setattr(
        "youtube_transcript_api.proxies.WebshareProxyConfig",
        _FakeWebshareProxyConfig,
    )

    transcript = fetch_transcript(
        "abc123",
        proxy_settings=WebshareProxySettings(
            enabled=True,
            proxy_username="proxy-user",
            proxy_password="proxy-pass",
        ),
    )

    assert transcript == "proxied transcript"
    proxy_config = captured["proxy_config"]
    assert isinstance(proxy_config, _FakeWebshareProxyConfig)
    assert proxy_config.proxy_username == "proxy-user"
    assert proxy_config.proxy_password == "proxy-pass"


def test_fetch_transcript_raises_clear_error_when_proxy_credentials_missing() -> None:
    with pytest.raises(
        TranscriptApiConfigError,
        match="Webshare proxy is enabled but WEBSHARE_PROXY_USERNAME or WEBSHARE_PROXY_PASSWORD is missing",
    ):
        fetch_transcript(
            "abc123",
            proxy_settings=WebshareProxySettings(enabled=True, proxy_username=None, proxy_password=None),
        )
