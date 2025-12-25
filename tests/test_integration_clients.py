"""Integration tests for Pipedream and Composio clients."""

import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch

from neurocluster.api.pipedream import PipedreamClient, PipedreamProfile, CreateProfileRequest
from neurocluster.api.composio import ComposioClient, ComposioProfile


class TestPipedreamClient:
    """Tests for PipedreamClient."""

    def test_client_initialization(self):
        """Test PipedreamClient initialization."""
        client = PipedreamClient(
            base_url="https://api.example.com/api",
            auth_token="test-token"
        )
        
        assert client.base_url == "https://api.example.com/api"
        assert client.timeout == 30.0
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_get_apps(self):
        """Test getting Pipedream apps."""
        client = PipedreamClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "apps": [{"slug": "slack", "name": "Slack"}],
            "total": 1
        }
        
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            result = await client.get_apps(q="slack")
            
            assert "apps" in result
            assert len(result["apps"]) == 1
            mock_req.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_profile(self):
        """Test creating a Pipedream profile."""
        client = PipedreamClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "profile_id": "profile_123",
            "profile_name": "Test Profile",
            "app_slug": "slack",
            "app_name": "Slack",
            "is_active": True,
            "is_default": False
        }
        
        request = CreateProfileRequest(
            profile_name="Test Profile",
            app_slug="slack",
            app_name="Slack",
            enabled_tools=["send_message"]
        )
        
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            profile = await client.create_profile(request)
            
            assert isinstance(profile, PipedreamProfile)
            assert profile.profile_id == "profile_123"
            assert profile.profile_name == "Test Profile"
            mock_req.assert_called_once()


class TestComposioClient:
    """Tests for ComposioClient."""

    def test_client_initialization(self):
        """Test ComposioClient initialization."""
        client = ComposioClient(
            base_url="https://api.example.com/api",
            auth_token="test-token"
        )
        
        assert client.base_url == "https://api.example.com/api"
        assert client.timeout == 30.0
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_get_toolkits(self):
        """Test getting Composio toolkits."""
        client = ComposioClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "toolkits": [{"slug": "slack", "name": "Slack"}],
            "total_items": 1
        }
        
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            result = await client.get_toolkits(search="slack")
            
            assert result["success"] is True
            assert len(result["toolkits"]) == 1
            mock_req.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_profile(self):
        """Test creating a Composio profile."""
        client = ComposioClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "profile_id": "profile_123",
            "profile_name": "Test Profile",
            "display_name": "Test",
            "toolkit_slug": "slack",
            "toolkit_name": "Slack",
            "mcp_url": "https://mcp.example.com",
            "is_connected": False,
            "is_default": False
        }
        
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            profile = await client.create_profile(
                toolkit_slug="slack",
                profile_name="Test Profile"
            )
            
            assert isinstance(profile, ComposioProfile)
            assert profile.profile_id == "profile_123"
            assert profile.profile_name == "Test Profile"
            mock_req.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_profiles(self):
        """Test getting Composio profiles."""
        client = ComposioClient(base_url="https://api.example.com/api")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "profiles": [
                {
                    "profile_id": "profile_123",
                    "profile_name": "Test Profile",
                    "display_name": "Test",
                    "toolkit_slug": "slack",
                    "toolkit_name": "Slack",
                    "mcp_url": "https://mcp.example.com",
                    "is_connected": True,
                    "is_default": False
                }
            ]
        }
        
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            profiles = await client.get_profiles(toolkit_slug="slack")
            
            assert len(profiles) == 1
            assert isinstance(profiles[0], ComposioProfile)
            assert profiles[0].profile_id == "profile_123"
            mock_req.assert_called_once()

