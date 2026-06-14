"""Retry helper with exponential backoff + jitter for async callables."""
import asyncio
import logging
import random
from functools import wraps
from typing import Awaitable, Callable, Iterable, Type

log = logging.getLogger(__name__)

# Common retryable conditions for HTTP/LLM calls.
DEFAULT_RETRYABLE: tuple = (
    asyncio.TimeoutError,
    ConnectionError,
)


def retry_async(
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    retryable: Iterable[Type[BaseException]] = DEFAULT_RETRYABLE,
    on_retry: Callable[[int, BaseException], None] | None = None,
):
    """Decorator that retries an async function with exponential backoff + jitter.

    Retries are bounded; the original exception is re-raised after the final attempt.
    """
    retryable_t = tuple(retryable)

    def deco(fn: Callable[..., Awaitable]):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                attempt += 1
                try:
                    return await fn(*args, **kwargs)
                except retryable_t as e:
                    if attempt >= max_attempts:
                        log.warning("retry_async: giving up after %d attempts on %s: %s", attempt, fn.__name__, e)
                        raise
                    sleep_for = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    sleep_for *= random.uniform(0.7, 1.3)  # jitter
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception:
                            pass
                    log.info("retry_async: %s attempt %d failed (%s); sleeping %.2fs", fn.__name__, attempt, type(e).__name__, sleep_for)
                    await asyncio.sleep(sleep_for)
        return wrapper
    return deco
