"""Base API client class for all NeuroCluster API clients."""

import logging
from typing import Optional, Dict, TYPE_CHECKING
import httpx

from .serialization import handle_api_response
from .constants import APIHeaders, ContentTypes
from .retry import retry_with_backoff

if TYPE_CHECKING:
    from .rate_limit import RateLimiter

# SDK-wide logger
logger = logging.getLogger("neurocluster.api")


class BaseAPIClient:
    """Base class for all API clients providing common functionality.
    
    This class handles:
    - HTTP client initialization with consistent headers
    - Authentication token management
    - Custom headers support
    - Context manager support (async with)
    - Standardized error handling
    """
    
    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 2.0,
        rate_limiter: Optional["RateLimiter"] = None,
    ):
        """Initialize the base API client.
        
        Args:
            base_url: Base URL of the API (e.g., "https://api.neurocluster.com/api")
            auth_token: Optional JWT token for authentication
            custom_headers: Optional additional headers to include in all requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for transient failures (default: 3)
            retry_backoff_factor: Backoff factor for retry delays (default: 2.0)
            rate_limiter: Optional RateLimiter instance for rate limiting requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self._rate_limiter = rate_limiter
        
        # Build headers with auth and custom headers
        headers = self._build_headers(auth_token, custom_headers)
        # Preserve canonical header casing for `headers` property/tests.
        # httpx normalizes header keys internally (e.g. lowercasing), but we want
        # to expose the logical headers the client was configured with.
        self._headers: Dict[str, str] = dict(headers)
        
        # Configure connection pooling for better performance
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0,
        )
        
        # Create httpx client with configured headers, timeout, and connection limits
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
            base_url=self.base_url,
            limits=limits,
        )
        # Expose limits for introspection/tests.
        setattr(self.client, "_limits", limits)
    
    def _build_headers(
        self, 
        auth_token: Optional[str], 
        custom_headers: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        """Build headers with auth and custom headers.
        
        Args:
            auth_token: Optional authentication token
            custom_headers: Optional custom headers
            
        Returns:
            Dictionary of headers
        """
        headers = {
            APIHeaders.CONTENT_TYPE: ContentTypes.JSON,
            APIHeaders.ACCEPT: ContentTypes.JSON,
        }
        
        if auth_token:
            headers[APIHeaders.API_KEY] = auth_token
        
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get the current headers configured for this client."""
        return dict(self._headers)
    
    async def close(self):
        """Close the httpx client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _handle_response(self, response: httpx.Response) -> Dict:
        """Handle API response and raise appropriate exceptions.
        
        This is a convenience method that delegates to the shared
        handle_api_response function.
        
        Args:
            response: HTTP response from httpx
            
        Returns:
            JSON data from response
            
        Raises:
            ValueError: For 404 Not Found errors
            PermissionError: For 403 Forbidden errors
            httpx.HTTPStatusError: For other HTTP errors
        """
        logger.debug(f"Response status: {response.status_code} for {response.request.method} {response.request.url}")
        if response.status_code >= 400:
            logger.warning(f"Request failed with status {response.status_code}: {response.text[:200]}")
        return handle_api_response(response)
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make an HTTP request with automatic retry for transient failures.
        
        If a rate limiter is configured, it will be used to throttle requests.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: URL path (relative to base_url)
            **kwargs: Additional arguments to pass to httpx client
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPStatusError: For non-retryable HTTP errors
            httpx.RequestError: For network errors after all retries exhausted
        """
        logger.debug(f"{method} {url}")
        
        async def _make_request():
            if self._rate_limiter is not None:
                async with self._rate_limiter.acquire():
                    return await self.client.request(method, url, **kwargs)
            return await self.client.request(method, url, **kwargs)
        
        return await retry_with_backoff(
            _make_request,
            max_retries=self.max_retries,
            backoff_factor=self.retry_backoff_factor,
        )

