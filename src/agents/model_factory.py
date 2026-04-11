from __future__ import annotations

import os

from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI


DEFAULT_AGENT_MODEL = "gpt-4.1"


def _get_optional_env(name: str) -> str | None:
    """Return a stripped env var value, treating empty strings as unset."""
    value = os.getenv(name)
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def build_openai_compatible_model(
    model_name: str | None = None,
) -> OpenAIChatCompletionsModel:
    """Build a chat completions model for OpenAI or any compatible provider."""
    configured_model = model_name or _get_optional_env("OPENAI_DEFAULT_MODEL") or DEFAULT_AGENT_MODEL
    api_key = _get_optional_env("OPENAI_API_KEY") or "unused"
    base_url = _get_optional_env("OPENAI_BASE_URL")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    return OpenAIChatCompletionsModel(
        model=configured_model,
        openai_client=client,
    )


def build_openai_model(model_name: str | None = None) -> OpenAIChatCompletionsModel:
    """Build a chat completions model pinned to OpenAI's default API endpoint."""
    configured_model = model_name or DEFAULT_AGENT_MODEL
    api_key = _get_optional_env("OPENAI_API_KEY") or "unused"
    client = AsyncOpenAI(api_key=api_key)

    return OpenAIChatCompletionsModel(
        model=configured_model,
        openai_client=client,
    )
