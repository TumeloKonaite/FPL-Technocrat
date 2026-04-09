from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar


T = TypeVar("T")


class RetryError(RuntimeError):
    """Raised when a retryable operation exhausts its attempts."""


@dataclass(frozen=True, slots=True)
class RetryConfig:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.25
    backoff_multiplier: float = 2.0


def retry_call(
    func: Callable[[], T],
    *,
    retry_on: tuple[type[BaseException], ...],
    context: str,
    config: RetryConfig | None = None,
) -> T:
    settings = config or RetryConfig()
    delay_seconds = settings.initial_delay_seconds
    last_error: BaseException | None = None

    for attempt in range(1, settings.max_attempts + 1):
        try:
            return func()
        except retry_on as exc:
            last_error = exc
            if attempt >= settings.max_attempts:
                break
            time.sleep(delay_seconds)
            delay_seconds *= settings.backoff_multiplier

    if last_error is None:
        raise RetryError(f"{context} failed without raising a retryable exception.")

    raise RetryError(
        f"{context} failed after {settings.max_attempts} attempt(s): {last_error}"
    ) from last_error
