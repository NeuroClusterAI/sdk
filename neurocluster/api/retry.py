"""Retry logic for transient failures."""

import asyncio
import logging
from typing import Callable, TypeVar, Optional, List
import httpx

# Use SDK-wide logger for consistent log hierarchy
logger = logging.getLogger("neurocluster.api.retry")

T = TypeVar("T")

# HTTP status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Network exceptions that should trigger a retry
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.NetworkError,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
)


async def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_status_codes: Optional[List[int]] = None,
    retryable_exceptions: Optional[tuple] = None,
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        backoff_factor: Factor to multiply delay by after each retry
        retryable_status_codes: List of HTTP status codes that should trigger retry
        retryable_exceptions: Tuple of exception types that should trigger retry
        
    Returns:
        Result of the function call
        
    Raises:
        Last exception raised by the function if all retries fail
    """
    if retryable_status_codes is None:
        retryable_status_codes = list(RETRYABLE_STATUS_CODES)
    if retryable_exceptions is None:
        retryable_exceptions = RETRYABLE_EXCEPTIONS
    
    last_exception = None
    delay = initial_delay
    
    for attempt in range(max_retries + 1):
        try:
            result = await func()
            
            # Check if result is an httpx.Response with retryable status
            if isinstance(result, httpx.Response):
                if result.status_code in retryable_status_codes:
                    if attempt < max_retries:
                        logger.warning(
                            f"Retryable status code {result.status_code} received. "
                            f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                        continue
                    else:
                        # Last attempt, return the response
                        return result
                else:
                    # Non-retryable status code, return immediately
                    return result
            
            # Success - return result
            return result
            
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Retryable exception {type(e).__name__} occurred. "
                    f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
            else:
                logger.error(
                    f"All {max_retries + 1} retry attempts failed. "
                    f"Last exception: {type(e).__name__}: {str(e)}"
                )
                raise
        
        except Exception as e:
            # Non-retryable exception - raise immediately
            logger.error(f"Non-retryable exception occurred: {type(e).__name__}: {str(e)}")
            raise
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    
    raise RuntimeError("Retry logic failed unexpectedly")

