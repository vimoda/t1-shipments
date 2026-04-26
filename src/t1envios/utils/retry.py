from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def with_backoff(
    fn: Callable[[], T],
    retries: int = 3,
    base_delay: float = 1.0,
    backoff: float = 2.0,
) -> T:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(base_delay * (backoff**attempt))
    raise last_exc  # type: ignore[misc]
