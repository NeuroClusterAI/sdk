"""Composio API client for managing Composio integrations."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import httpx

from .base_client import BaseAPIClient
from .serialization import to_dict, from_dict


@dataclass
class ComposioToolkit:
    """Composio toolkit information."""
    slug: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None


@dataclass
class ComposioProfile:
    """Composio credential profile."""
    profile_id: str
    profile_name: str
    display_name: str
    toolkit_slug: str
    toolkit_name: str
    mcp_url: str
    redirect_url: Optional[str] = None
    connected_account_id: Optional[str] = None
    is_connected: bool = False
    is_default: bool = False
    created_at: Optional[str] = None


@dataclass
class IntegrationStatus:
    """Composio integration status."""
    status: str
    toolkit: str
    auth_config_id: str
    connected_account_id: str
    mcp_server_id: str
    final_mcp_url: str
    profile_id: Optional[str] = None
    redirect_url: Optional[str] = None


@dataclass
class ComposioTool:
    """Composio tool information."""
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None


class ComposioClient(BaseAPIClient):
    """Client for interacting with Composio API."""

    async def get_categories(self) -> Dict[str, Any]:
        """
        Get list of available Composio categories.

        Returns:
            Dictionary containing categories list
        """
        response = await self._request_with_retry("GET", "/composio/categories")
        return self._handle_response(response)

    async def get_toolkits(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get list of available Composio toolkits.

        Args:
            limit: Maximum number of toolkits to return (max 500)
            cursor: Cursor for pagination
            search: Search query
            category: Filter by category

        Returns:
            Dictionary containing toolkits list and pagination info
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if search:
            params["search"] = search
        if category:
            params["category"] = category

        response = await self._request_with_retry("GET", "/composio/toolkits", params=params)
        return self._handle_response(response)

    async def get_toolkit_details(self, toolkit_slug: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific toolkit.

        Args:
            toolkit_slug: The toolkit slug identifier

        Returns:
            Dictionary containing toolkit details
        """
        response = await self._request_with_retry("GET", f"/composio/toolkits/{toolkit_slug}/details")
        return self._handle_response(response)

    async def get_tools(
        self,
        toolkit_slug: str,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get available tools for a Composio toolkit.

        Args:
            toolkit_slug: The toolkit slug identifier
            limit: Maximum number of tools to return
            cursor: Cursor for pagination

        Returns:
            Dictionary containing tools list
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        response = await self._request_with_retry(
            "POST",
            f"/composio/toolkits/{toolkit_slug}/tools",
            json={"limit": limit, "cursor": cursor} if cursor else {"limit": limit},
        )
        return self._handle_response(response)

    async def integrate_toolkit(
        self,
        toolkit_slug: str,
        profile_name: Optional[str] = None,
        display_name: Optional[str] = None,
        mcp_server_name: Optional[str] = None,
        save_as_profile: bool = True,
    ) -> IntegrationStatus:
        """
        Integrate a Composio toolkit.

        Args:
            toolkit_slug: Toolkit slug to integrate
            profile_name: Optional profile name
            display_name: Optional display name
            mcp_server_name: Optional MCP server name
            save_as_profile: Whether to save as profile

        Returns:
            IntegrationStatus with integration details
        """
        payload = {
            "toolkit_slug": toolkit_slug,
            "save_as_profile": save_as_profile,
        }
        if profile_name:
            payload["profile_name"] = profile_name
        if display_name:
            payload["display_name"] = display_name
        if mcp_server_name:
            payload["mcp_server_name"] = mcp_server_name

        response = await self._request_with_retry("POST", "/composio/integrate", json=payload)
        data = self._handle_response(response)
        return from_dict(IntegrationStatus, data)

    async def create_profile(
        self,
        toolkit_slug: str,
        profile_name: str,
        display_name: Optional[str] = None,
        mcp_server_name: Optional[str] = None,
        is_default: bool = False,
        initiation_fields: Optional[Dict[str, str]] = None,
        custom_auth_config: Optional[Dict[str, str]] = None,
        use_custom_auth: bool = False,
    ) -> ComposioProfile:
        """
        Create a new Composio profile.

        Args:
            toolkit_slug: Toolkit slug
            profile_name: Profile name
            display_name: Optional display name
            mcp_server_name: Optional MCP server name
            is_default: Whether this is the default profile
            initiation_fields: Optional initiation fields for OAuth
            custom_auth_config: Optional custom auth configuration
            use_custom_auth: Whether to use custom auth

        Returns:
            Created ComposioProfile object
        """
        payload = {
            "toolkit_slug": toolkit_slug,
            "profile_name": profile_name,
            "is_default": is_default,
            "use_custom_auth": use_custom_auth,
        }
        if display_name:
            payload["display_name"] = display_name
        if mcp_server_name:
            payload["mcp_server_name"] = mcp_server_name
        if initiation_fields:
            payload["initiation_fields"] = initiation_fields
        if custom_auth_config:
            payload["custom_auth_config"] = custom_auth_config

        response = await self._request_with_retry("POST", "/composio/profiles", json=payload)
        data = self._handle_response(response)
        return from_dict(ComposioProfile, data)

    async def get_profiles(
        self, toolkit_slug: Optional[str] = None
    ) -> List[ComposioProfile]:
        """
        Get list of Composio profiles.

        Args:
            toolkit_slug: Optional filter by toolkit slug

        Returns:
            List of ComposioProfile objects
        """
        params = {}
        if toolkit_slug:
            params["toolkit_slug"] = toolkit_slug

        response = await self._request_with_retry("GET", "/composio/profiles", params=params)
        data = self._handle_response(response)
        profiles_data = data.get("profiles", [])
        return [from_dict(ComposioProfile, profile) for profile in profiles_data]

    async def get_profile(self, profile_id: str) -> ComposioProfile:
        """
        Get a specific Composio profile by ID.

        Args:
            profile_id: Profile identifier

        Returns:
            ComposioProfile object
        """
        response = await self._request_with_retry("GET", f"/composio/profiles/{profile_id}")
        data = self._handle_response(response)
        return from_dict(ComposioProfile, data)

    async def get_profile_mcp_config(self, profile_id: str) -> Dict[str, Any]:
        """
        Get MCP configuration for a profile.

        Args:
            profile_id: Profile identifier

        Returns:
            Dictionary containing MCP configuration
        """
        response = await self._request_with_retry("GET", f"/composio/profiles/{profile_id}/mcp-config")
        return self._handle_response(response)

    async def discover_tools(self, profile_id: str) -> Dict[str, Any]:
        """
        Discover available tools for a Composio profile.

        Args:
            profile_id: Profile identifier

        Returns:
            Dictionary containing discovered tools
        """
        response = await self._request_with_retry(
            "POST", f"/composio/profiles/{profile_id}/discover-tools"
        )
        return self._handle_response(response)

    async def check_profile_name_availability(
        self, toolkit_slug: str, profile_name: str
    ) -> Dict[str, Any]:
        """
        Check if a profile name is available.

        Args:
            toolkit_slug: Toolkit slug
            profile_name: Profile name to check

        Returns:
            Dictionary with availability status
        """
        params = {"toolkit_slug": toolkit_slug, "profile_name": profile_name}
        response = await self._request_with_retry(
            "GET", "/composio/profiles/check-name-availability", params=params
        )
        return self._handle_response(response)

    async def get_integration_status(
        self, connected_account_id: str
    ) -> Dict[str, Any]:
        """
        Get integration status for a connected account.

        Args:
            connected_account_id: Connected account identifier

        Returns:
            Dictionary containing integration status
        """
        response = await self._request_with_retry(
            "GET", f"/composio/integration/{connected_account_id}/status"
        )
        return self._handle_response(response)


def create_composio_client(
    base_url: str,
    auth_token: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
) -> ComposioClient:
    """
    Create a ComposioClient instance.

    Args:
        base_url: Base URL of the API
        auth_token: JWT token for authentication
        custom_headers: Additional headers to include in all requests
        timeout: Request timeout in seconds

    Returns:
        ComposioClient instance
    """
    return ComposioClient(
        base_url=base_url,
        auth_token=auth_token,
        custom_headers=custom_headers,
        timeout=timeout,
    )

