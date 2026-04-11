from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.agents.model_factory import (
    DEFAULT_AGENT_MODEL,
    build_openai_compatible_model,
    build_openai_model,
)


def test_build_openai_compatible_model_uses_default_configuration() -> None:
    fake_model = MagicMock(name="model")

    with (
        patch.dict("os.environ", {}, clear=True),
        patch("src.agents.model_factory.AsyncOpenAI") as mock_client_class,
        patch(
            "src.agents.model_factory.OpenAIChatCompletionsModel",
            return_value=fake_model,
        ) as mock_model_class,
    ):
        client = mock_client_class.return_value

        result = build_openai_compatible_model()

    assert result is fake_model
    mock_client_class.assert_called_once_with(api_key="unused", base_url=None)
    mock_model_class.assert_called_once_with(
        model=DEFAULT_AGENT_MODEL,
        openai_client=client,
    )


def test_build_openai_compatible_model_uses_configured_provider() -> None:
    fake_model = MagicMock(name="model")
    env = {
        "OPENAI_API_KEY": "provider-key",
        "OPENAI_BASE_URL": "https://api.ollama.ai/v1",
        "OPENAI_DEFAULT_MODEL": "llama3.3:70b",
    }

    with (
        patch.dict("os.environ", env, clear=True),
        patch("src.agents.model_factory.AsyncOpenAI") as mock_client_class,
        patch(
            "src.agents.model_factory.OpenAIChatCompletionsModel",
            return_value=fake_model,
        ) as mock_model_class,
    ):
        client = mock_client_class.return_value

        result = build_openai_compatible_model()

    assert result is fake_model
    mock_client_class.assert_called_once_with(
        api_key="provider-key",
        base_url="https://api.ollama.ai/v1",
    )
    mock_model_class.assert_called_once_with(
        model="llama3.3:70b",
        openai_client=client,
    )


def test_build_openai_compatible_model_prefers_explicit_model_name() -> None:
    fake_model = MagicMock(name="model")
    env = {
        "OPENAI_API_KEY": "provider-key",
        "OPENAI_DEFAULT_MODEL": "ignored-model",
    }

    with (
        patch.dict("os.environ", env, clear=True),
        patch("src.agents.model_factory.AsyncOpenAI") as mock_client_class,
        patch(
            "src.agents.model_factory.OpenAIChatCompletionsModel",
            return_value=fake_model,
        ) as mock_model_class,
    ):
        client = mock_client_class.return_value

        result = build_openai_compatible_model("explicit-model")

    assert result is fake_model
    mock_client_class.assert_called_once_with(api_key="provider-key", base_url=None)
    mock_model_class.assert_called_once_with(
        model="explicit-model",
        openai_client=client,
    )


def test_build_openai_model_ignores_compatible_provider_overrides() -> None:
    fake_model = MagicMock(name="model")
    env = {
        "OPENAI_API_KEY": "openai-key",
        "OPENAI_BASE_URL": "https://ollama.com/v1",
        "OPENAI_DEFAULT_MODEL": "glm-4.7:cloud",
    }

    with (
        patch.dict("os.environ", env, clear=True),
        patch("src.agents.model_factory.AsyncOpenAI") as mock_client_class,
        patch(
            "src.agents.model_factory.OpenAIChatCompletionsModel",
            return_value=fake_model,
        ) as mock_model_class,
    ):
        client = mock_client_class.return_value

        result = build_openai_model()

    assert result is fake_model
    mock_client_class.assert_called_once_with(api_key="openai-key")
    mock_model_class.assert_called_once_with(
        model=DEFAULT_AGENT_MODEL,
        openai_client=client,
    )
