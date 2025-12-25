"""Rate limiting support for API calls."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

logger = logging.getLogger("neurocluster.api.rate_limit")


class RateLimiter:
    """
    Simple rate limiter for API calls using a sliding window approach.
    
    This limiter uses a semaphore to control concurrent requests and
    a minimum interval between requests.
    
    Usage:
        limiter = RateLimiter(max_concurrent=10, requests_per_second=5.0)
        
        async with limiter.acquire():
            # Make API request
            response = await client.get("/endpoint")
    
    Args:
        max_concurrent: Maximum number of concurrent requests allowed
        requests_per_second: Maximum requests per second (determines minimum interval)
    """
    
    def __init__(
        self, 
        max_concurrent: int = 10, 
        requests_per_second: float = 10.0
    ):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()
        self._max_concurrent = max_concurrent
        self._requests_per_second = requests_per_second
    
    @property
    def max_concurrent(self) -> int:
        """Maximum concurrent requests allowed."""
        return self._max_concurrent
    
    @property
    def requests_per_second(self) -> float:
        """Maximum requests per second."""
        return self._requests_per_second
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a rate limit slot.
        
        This context manager:
        1. Acquires a semaphore slot (blocks if at max_concurrent)
        2. Waits for the minimum interval since the last request
        3. Yields control to the caller
        4. Releases the semaphore slot on exit
        
        Yields:
            None - caller can make their request
        """
        async with self._semaphore:
            async with self._lock:
                now = time.monotonic()
                wait_time = self._last_request_time + self._interval - now
                
                if wait_time > 0:
                    logger.debug(f"Rate limiting: waiting {wait_time:.3f}s")
                    await asyncio.sleep(wait_time)
                
                self._last_request_time = time.monotonic()
            
            yield


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts based on 429 (Too Many Requests) responses.
    
    When a 429 is encountered, the limiter backs off by reducing the
    requests_per_second rate. It gradually recovers over time.
    
    Args:
        max_concurrent: Maximum number of concurrent requests allowed
        requests_per_second: Starting requests per second
        min_requests_per_second: Minimum requests per second (floor)
        backoff_factor: Factor to reduce rate by on 429
        recovery_factor: Factor to increase rate by on success
        recovery_interval: Minimum seconds between rate recovery attempts
    """
    
    def __init__(
        self,
        max_concurrent: int = 10,
        requests_per_second: float = 10.0,
        min_requests_per_second: float = 1.0,
        backoff_factor: float = 0.5,
        recovery_factor: float = 1.1,
        recovery_interval: float = 60.0,
    ):
        super().__init__(max_concurrent, requests_per_second)
        self._initial_rate = requests_per_second
        self._min_rate = min_requests_per_second
        self._backoff_factor = backoff_factor
        self._recovery_factor = recovery_factor
        self._recovery_interval = recovery_interval
        self._last_recovery_attempt: float = 0.0
        self._current_rate = requests_per_second
    
    async def on_rate_limited(self):
        """
        Call this when a 429 response is received.
        
        Reduces the rate by the backoff factor.
        """
        async with self._lock:
            old_rate = self._current_rate
            self._current_rate = max(
                self._current_rate * self._backoff_factor,
                self._min_rate
            )
            self._interval = 1.0 / self._current_rate
            logger.warning(
                f"Rate limited (429). Reducing rate from {old_rate:.2f} "
                f"to {self._current_rate:.2f} req/s"
            )
    
    async def on_success(self):
        """
        Call this after a successful request.
        
        Attempts to gradually recover the rate if enough time has passed.
        """
        async with self._lock:
            now = time.monotonic()
            
            # Only attempt recovery if enough time has passed
            if now - self._last_recovery_attempt < self._recovery_interval:
                return
            
            # Only recover if we're below initial rate
            if self._current_rate >= self._initial_rate:
                return
            
            old_rate = self._current_rate
            self._current_rate = min(
                self._current_rate * self._recovery_factor,
                self._initial_rate
            )
            self._interval = 1.0 / self._current_rate
            self._last_recovery_attempt = now
            
            logger.debug(
                f"Recovering rate from {old_rate:.2f} "
                f"to {self._current_rate:.2f} req/s"
            )
    
    @property
    def current_rate(self) -> float:
        """Current effective requests per second."""
        return self._current_rate

