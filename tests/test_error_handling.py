"""Unit tests for error handling across clients."""

import pytest
import httpx
from unittest.mock import Mock

from neurocluster.api.base_client import BaseAPIClient
from neurocluster.api.agents import AgentsClient
from neurocluster.api.threads import ThreadsClient
from neurocluster.api.versions import VersionsClient


class TestErrorHandling:
    """Tests for consistent error handling across all clients."""

    def test_404_error_raises_value_error(self):
        """Test that 404 errors raise ValueError consistently."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Resource not found"}
        mock_response.text = "Resource not found"
        
        with pytest.raises(ValueError, match="Resource not found"):
            client._handle_response(mock_response)

    def test_403_error_raises_permission_error(self):
        """Test that 403 errors raise PermissionError consistently."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {"detail": "Access denied"}
        mock_response.text = "Access denied"
        
        with pytest.raises(PermissionError, match="Access denied"):
            client._handle_response(mock_response)

    def test_500_error_raises_http_status_error(self):
        """Test that 500+ errors raise HTTPStatusError."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_response.text = "Internal server error"
        mock_response.request = Mock()
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client._handle_response(mock_response)
        
        assert "500" in str(exc_info.value)

    def test_all_clients_inherit_error_handling(self):
        """Test that all clients inherit consistent error handling."""
        base_url = "https://api.example.com/api"
        auth_token = "test-token"
        
        agents_client = AgentsClient(base_url, auth_token)
        threads_client = ThreadsClient(base_url, auth_token)
        versions_client = VersionsClient(base_url, auth_token)
        
        # All should have the same _handle_response method
        assert hasattr(agents_client, "_handle_response")
        assert hasattr(threads_client, "_handle_response")
        assert hasattr(versions_client, "_handle_response")
        
        # Test that they all raise the same errors
        mock_response_404 = Mock(spec=httpx.Response)
        mock_response_404.status_code = 404
        mock_response_404.json.return_value = {"detail": "Not found"}
        mock_response_404.text = "Not found"
        
        for client in [agents_client, threads_client, versions_client]:
            with pytest.raises(ValueError):
                client._handle_response(mock_response_404)

    def test_error_without_detail_field(self):
        """Test error handling when detail field is missing."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Error occurred"}
        mock_response.text = "Error occurred"
        mock_response.request = Mock()
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client._handle_response(mock_response)
        
        assert "500" in str(exc_info.value)

    def test_error_with_invalid_json(self):
        """Test error handling when response JSON is invalid."""
        client = BaseAPIClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Error message"
        mock_response.request = Mock()
        
        with pytest.raises(httpx.HTTPStatusError):
            client._handle_response(mock_response)

