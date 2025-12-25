"""Unit tests for retry logic."""

import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from neurocluster.api.retry import retry_with_backoff, RETRYABLE_STATUS_CODES, RETRYABLE_EXCEPTIONS


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_successful_request_no_retry(self):
        """Test that successful requests don't trigger retries."""
        async def success_func():
            return "success"
        
        result = await retry_with_backoff(success_func, max_retries=3)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_retryable_status_code(self):
        """Test retry on retryable HTTP status codes."""
        attempt_count = 0
        
        async def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            response = Mock(spec=httpx.Response)
            response.status_code = 500 if attempt_count < 3 else 200
            return response
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await retry_with_backoff(failing_func, max_retries=3, initial_delay=0.01)
            assert attempt_count == 3
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """Test retry on network errors."""
        attempt_count = 0
        
        async def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise httpx.NetworkError("Connection failed")
            return "success"
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await retry_with_backoff(failing_func, max_retries=3, initial_delay=0.01)
            assert attempt_count == 3
            assert result == "success"

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries."""
        async def always_failing_func():
            raise httpx.NetworkError("Connection failed")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(httpx.NetworkError):
                await retry_with_backoff(always_failing_func, max_retries=2, initial_delay=0.01)

    @pytest.mark.asyncio
    async def test_non_retryable_exception_raises_immediately(self):
        """Test that non-retryable exceptions raise immediately."""
        async def failing_func():
            raise ValueError("Non-retryable error")
        
        with pytest.raises(ValueError):
            await retry_with_backoff(failing_func, max_retries=3)

    @pytest.mark.asyncio
    async def test_backoff_delay_increases(self):
        """Test that delay increases with backoff factor."""
        delays = []
        real_sleep = asyncio.sleep
        
        async def sleep_mock(delay):
            delays.append(delay)
            # Yield control without recursing into the patched asyncio.sleep
            await real_sleep(0)
        
        attempt_count = 0
        
        async def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise httpx.NetworkError("Connection failed")
            return "success"
        
        with patch('asyncio.sleep', side_effect=sleep_mock):
            await retry_with_backoff(
                failing_func,
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=2.0,
            )
        
        # Should have 2 retries with delays 1.0 and 2.0
        assert len(delays) == 2
        assert delays[0] == 1.0
        assert delays[1] == 2.0

    @pytest.mark.asyncio
    async def test_max_delay_respected(self):
        """Test that max_delay is respected."""
        delays = []
        real_sleep = asyncio.sleep
        
        async def sleep_mock(delay):
            delays.append(delay)
            await real_sleep(0)
        
        attempt_count = 0
        
        async def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 4:
                raise httpx.NetworkError("Connection failed")
            return "success"
        
        with patch('asyncio.sleep', side_effect=sleep_mock):
            await retry_with_backoff(
                failing_func,
                max_retries=4,
                initial_delay=10.0,
                max_delay=20.0,
                backoff_factor=2.0,
            )
        
        # Delays should be: 10, 20, 20 (capped at max_delay)
        assert len(delays) == 3
        assert all(d <= 20.0 for d in delays)
        assert delays[-1] == 20.0

    @pytest.mark.asyncio
    async def test_429_rate_limit_retry(self):
        """Test that 429 (rate limit) triggers retry."""
        attempt_count = 0
        
        async def rate_limited_func():
            nonlocal attempt_count
            attempt_count += 1
            response = Mock(spec=httpx.Response)
            response.status_code = 429 if attempt_count < 2 else 200
            return response
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await retry_with_backoff(rate_limited_func, max_retries=3, initial_delay=0.01)
            assert attempt_count == 2
            assert result.status_code == 200

