"""
Utilities Module.

Provides shared helper functions including asynchronous retries, rate-limiting,
concurrency management, text parsing, and serialization.
"""

import asyncio
import functools
import random
import time
from typing import Any, Callable, TypeVar, cast
from core.logger import logger

F = TypeVar("F", bound=Callable[..., Any])


def retry_async(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """Decorator to retry asynchronous operations with exponential backoff and jitter.

    Args:
        max_retries: Maximum number of retries.
        initial_delay: Baseline time to sleep between attempts (in seconds).
        backoff_factor: Multiplier to apply to delay on consecutive failures.
        jitter: Whether to add random variance (noise) to the backoff delay.
        exceptions: Tuple of exceptions to intercept and trigger retries on.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries. "
                            f"Error: {str(e)}"
                        )
                        break

                    # Calculate exponential backoff
                    sleep_time = delay
                    if jitter:
                        sleep_time = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} for '{func.__name__}' failed with: {str(e)}. "
                        f"Retrying in {sleep_time:.2f} seconds..."
                    )
                    
                    await asyncio.sleep(sleep_time)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception

        return cast(F, wrapper)
    return decorator


class AsyncRateLimiter:
    """A leaky-bucket token rate limiter for managing async web requests."""

    def __init__(self, requests_per_second: float = 2.0):
        """Initialize the rate limiter.

        Args:
            requests_per_second: Maximum allowed queries per second.
        """
        self.rate = requests_per_second
        self.token_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0.0
        self.last_time = time.monotonic()
        self.tokens = requests_per_second
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token slot, yielding control (sleeping) if request capacity is full."""
        if self.rate <= 0:
            return

        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_time
            self.last_time = now
            
            # Replenish tokens
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            
            if self.tokens < 1.0:
                # Wait for token replenishment
                wait_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
                self.last_time = time.monotonic()
            else:
                self.tokens -= 1.0


def clean_text(text: str) -> str:
    """Normalize whitespace and clean up raw string inputs.

    Args:
        text: Raw text.

    Returns:
        Cleaned, normalized string.
    """
    if not text:
        return ""
    # Strip whitespace, replace line breaks and multiple spaces with a single space
    return " ".join(text.strip().split())
