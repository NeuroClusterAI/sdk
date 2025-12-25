"""Unit tests for BaseAPIClient."""

import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch

from neurocluster.api.base_client import BaseAPIClient
from neurocluster.api.constants import APIHeaders, ContentTypes


class TestBaseAPIClient:
    """Tests for BaseAPIClient class."""

    def test_initialization(self):
        """Test client initialization."""
        client = BaseAPIClient(
            base_url="https://api.example.com/api",
            auth_token="test-token",
            timeout=60.0
        )
        
        assert client.base_url == "https://api.example.com/api"
        assert client.timeout == 60.0
        assert client.client is not None

    def test_initialization_without_auth(self):
        """Test client initialization without auth token."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        assert client.base_url == "https://api.example.com/api"
        assert client.client is not None

    def test_initialization_with_custom_headers(self):
        """Test client initialization with custom headers."""
        custom_headers = {"X-Custom-Header": "custom-value"}
        client = BaseAPIClient(
            base_url="https://api.example.com/api",
            custom_headers=custom_headers
        )
        
        assert APIHeaders.CONTENT_TYPE in client.headers
        assert APIHeaders.ACCEPT in client.headers
        assert "X-Custom-Header" in client.headers
        assert client.headers["X-Custom-Header"] == "custom-value"

    def test_headers_property(self):
        """Test headers property returns dict."""
        client = BaseAPIClient(
            base_url="https://api.example.com/api",
            auth_token="test-token"
        )
        
        headers = client.headers
        
        assert isinstance(headers, dict)
        assert APIHeaders.API_KEY in headers
        assert headers[APIHeaders.API_KEY] == "test-token"

    def test_build_headers_with_auth(self):
        """Test _build_headers with auth token."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        headers = client._build_headers("test-token", None)
        
        assert headers[APIHeaders.API_KEY] == "test-token"
        assert headers[APIHeaders.CONTENT_TYPE] == ContentTypes.JSON
        assert headers[APIHeaders.ACCEPT] == ContentTypes.JSON

    def test_build_headers_without_auth(self):
        """Test _build_headers without auth token."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        headers = client._build_headers(None, None)
        
        assert APIHeaders.API_KEY not in headers
        assert headers[APIHeaders.CONTENT_TYPE] == ContentTypes.JSON

    def test_build_headers_with_custom(self):
        """Test _build_headers with custom headers."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        custom_headers = {"X-Custom": "value"}
        headers = client._build_headers("token", custom_headers)
        
        assert headers["X-Custom"] == "value"
        assert headers[APIHeaders.API_KEY] == "token"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        # Mock the close method
        client.close = AsyncMock()
        
        async with client:
            assert client is not None
        
        # Verify close was called
        client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close method."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        # Mock the httpx client's aclose
        client.client.aclose = AsyncMock()
        
        await client.close()
        
        client.client.aclose.assert_called_once()

    def test_handle_response_success(self):
        """Test _handle_response with successful response."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        
        result = client._handle_response(mock_response)
        
        assert result == {"data": "success"}

    def test_handle_response_error(self):
        """Test _handle_response with error response."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_response.text = "Not found"
        
        with pytest.raises(ValueError):
            client._handle_response(mock_response)

    def test_url_stripping(self):
        """Test that trailing slashes are stripped from base_url."""
        client = BaseAPIClient(base_url="https://api.example.com/api/")
        
        assert client.base_url == "https://api.example.com/api"

    def test_connection_limits(self):
        """Test that connection limits are configured."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        # Verify limits are set on the httpx client
        assert hasattr(client.client, "_limits")
        limits = client.client._limits
        assert limits.max_keepalive_connections == 20
        assert limits.max_connections == 100

