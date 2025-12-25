"""Pipedream API client for managing Pipedream integrations."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import httpx

from .base_client import BaseAPIClient
from .serialization import to_dict, from_dict


@dataclass
class PipedreamApp:
    """Pipedream app information."""
    slug: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None


@dataclass
class PipedreamProfile:
    """Pipedream credential profile."""
    profile_id: str
    profile_name: str
    app_slug: str
    app_name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    enabled_tools: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class MCPServer:
    """MCP server information."""
    app_slug: str
    app_name: str
    server_url: str
    project_id: Optional[str] = None
    environment: Optional[str] = None
    external_user_id: Optional[str] = None
    oauth_app_id: Optional[str] = None
    status: str = "connected"
    available_tools: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@dataclass
class MCPDiscoveryResponse:
    """MCP discovery response."""
    success: bool
    mcp_servers: List[MCPServer]
    count: int
    error: Optional[str] = None


@dataclass
class MCPConnectionResponse:
    """MCP connection response."""
    success: bool
    mcp_config: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ConnectionTokenResponse:
    """Connection token response."""
    success: bool
    link: Optional[str] = None
    token: Optional[str] = None
    external_user_id: str = ""
    app: Optional[str] = None
    expires_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CreateProfileRequest:
    """Request to create a Pipedream profile."""
    profile_name: str
    app_slug: str
    app_name: str
    description: Optional[str] = None
    is_default: bool = False
    oauth_app_id: Optional[str] = None
    enabled_tools: List[str] = None
    external_user_id: Optional[str] = None


@dataclass
class UpdateProfileRequest:
    """Request to update a Pipedream profile."""
    profile_name: Optional[str] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    enabled_tools: Optional[List[str]] = None


class PipedreamClient(BaseAPIClient):
    """Client for interacting with Pipedream API."""

    async def get_apps(
        self,
        after: Optional[str] = None,
        q: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get list of available Pipedream apps.

        Args:
            after: Cursor for pagination
            q: Search query
            category: Filter by category

        Returns:
            Dictionary containing apps list and pagination info
        """
        params = {}
        if after:
            params["after"] = after
        if q:
            params["q"] = q
        if category:
            params["category"] = category

        response = await self._request_with_retry("GET", "/pipedream/apps", params=params)
        return self._handle_response(response)

    async def get_app_tools(self, app_slug: str) -> Dict[str, Any]:
        """
        Get available tools for a Pipedream app.

        Args:
            app_slug: The app slug identifier

        Returns:
            Dictionary containing tools list
        """
        response = await self._request_with_retry("GET", f"/pipedream/apps/{app_slug}/tools")
        return self._handle_response(response)

    async def get_profiles(
        self,
        app_slug: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[PipedreamProfile]:
        """
        Get list of Pipedream credential profiles.

        Args:
            app_slug: Optional filter by app slug
            is_active: Optional filter by active status

        Returns:
            List of PipedreamProfile objects
        """
        params = {}
        if app_slug:
            params["app_slug"] = app_slug
        if is_active is not None:
            params["is_active"] = is_active

        response = await self._request_with_retry("GET", "/pipedream/profiles", params=params)
        data = self._handle_response(response)
        return [from_dict(PipedreamProfile, profile) for profile in data]

    async def get_profile(self, profile_id: str) -> PipedreamProfile:
        """
        Get a specific Pipedream profile by ID.

        Args:
            profile_id: Profile identifier

        Returns:
            PipedreamProfile object
        """
        response = await self._request_with_retry("GET", f"/pipedream/profiles/{profile_id}")
        data = self._handle_response(response)
        return from_dict(PipedreamProfile, data)

    async def create_profile(self, request: CreateProfileRequest) -> PipedreamProfile:
        """
        Create a new Pipedream credential profile.

        Args:
            request: CreateProfileRequest with profile details

        Returns:
            Created PipedreamProfile object
        """
        response = await self._request_with_retry(
            "POST", "/pipedream/profiles", json=to_dict(request)
        )
        data = self._handle_response(response)
        return from_dict(PipedreamProfile, data)

    async def update_profile(
        self, profile_id: str, request: UpdateProfileRequest
    ) -> PipedreamProfile:
        """
        Update an existing Pipedream profile.

        Args:
            profile_id: Profile identifier
            request: UpdateProfileRequest with updated fields

        Returns:
            Updated PipedreamProfile object
        """
        response = await self._request_with_retry(
            "PUT", f"/pipedream/profiles/{profile_id}", json=to_dict(request)
        )
        data = self._handle_response(response)
        return from_dict(PipedreamProfile, data)

    async def delete_profile(self, profile_id: str) -> None:
        """
        Delete a Pipedream profile.

        Args:
            profile_id: Profile identifier
        """
        response = await self._request_with_retry("DELETE", f"/pipedream/profiles/{profile_id}")
        self._handle_response(response)

    async def discover_mcp_servers(
        self, app_slug: Optional[str] = None, oauth_app_id: Optional[str] = None
    ) -> MCPDiscoveryResponse:
        """
        Discover available MCP servers for Pipedream.

        Args:
            app_slug: Optional app slug to filter by
            oauth_app_id: Optional OAuth app ID

        Returns:
            MCPDiscoveryResponse with available servers
        """
        payload = {}
        if app_slug:
            payload["app_slug"] = app_slug
        if oauth_app_id:
            payload["oauth_app_id"] = oauth_app_id

        response = await self._request_with_retry(
            "POST", "/pipedream/mcp/discover", json=payload
        )
        data = self._handle_response(response)
        return from_dict(MCPDiscoveryResponse, data)

    async def discover_mcp_servers_for_profile(
        self,
        external_user_id: str,
        app_slug: Optional[str] = None,
        oauth_app_id: Optional[str] = None,
    ) -> MCPDiscoveryResponse:
        """
        Discover MCP servers for a specific profile.

        Args:
            external_user_id: External user ID for the profile
            app_slug: Optional app slug to filter by
            oauth_app_id: Optional OAuth app ID

        Returns:
            MCPDiscoveryResponse with available servers
        """
        payload = {"external_user_id": external_user_id}
        if app_slug:
            payload["app_slug"] = app_slug
        if oauth_app_id:
            payload["oauth_app_id"] = oauth_app_id

        response = await self._request_with_retry(
            "POST", "/pipedream/mcp/discover-profile", json=payload
        )
        data = self._handle_response(response)
        return from_dict(MCPDiscoveryResponse, data)

    async def create_mcp_connection(
        self, app_slug: str, oauth_app_id: Optional[str] = None
    ) -> MCPConnectionResponse:
        """
        Create an MCP connection for a Pipedream app.

        Args:
            app_slug: App slug identifier
            oauth_app_id: Optional OAuth app ID

        Returns:
            MCPConnectionResponse with connection details
        """
        payload = {"app_slug": app_slug}
        if oauth_app_id:
            payload["oauth_app_id"] = oauth_app_id

        response = await self._request_with_retry(
            "POST", "/pipedream/mcp/connect", json=payload
        )
        data = self._handle_response(response)
        return from_dict(MCPConnectionResponse, data)

    async def create_connection_token(
        self, app: Optional[str] = None
    ) -> ConnectionTokenResponse:
        """
        Create a connection token for OAuth flow.

        Args:
            app: Optional app slug

        Returns:
            ConnectionTokenResponse with token and link
        """
        payload = {}
        if app:
            payload["app"] = app

        response = await self._request_with_retry(
            "POST", "/pipedream/connection-tokens", json=payload
        )
        data = self._handle_response(response)
        return from_dict(ConnectionTokenResponse, data)


def create_pipedream_client(
    base_url: str,
    auth_token: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
) -> PipedreamClient:
    """
    Create a PipedreamClient instance.

    Args:
        base_url: Base URL of the API
        auth_token: JWT token for authentication
        custom_headers: Additional headers to include in all requests
        timeout: Request timeout in seconds

    Returns:
        PipedreamClient instance
    """
    return PipedreamClient(
        base_url=base_url,
        auth_token=auth_token,
        custom_headers=custom_headers,
        timeout=timeout,
    )

