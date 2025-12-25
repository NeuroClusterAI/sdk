import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

from .agents import CustomMCP, AgentPressTools, AgentPress_ToolConfig
from .base_client import BaseAPIClient
from .serialization import to_dict as base_to_dict, from_dict as base_from_dict


@dataclass
class CreateVersionRequest:
    system_prompt: str
    model: Optional[str] = None
    configured_mcps: Optional[List[CustomMCP]] = None
    custom_mcps: Optional[List[CustomMCP]] = None
    agentpress_tools: Optional[Dict[AgentPressTools, AgentPress_ToolConfig]] = None
    version_name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class UpdateVersionDetailsRequest:
    version_name: Optional[str] = None
    change_description: Optional[str] = None


@dataclass
class VersionResponse:
    version_id: str
    agent_id: str
    version_number: int
    version_name: str
    system_prompt: str
    configured_mcps: List[Dict[str, Any]]
    custom_mcps: List[Dict[str, Any]]
    agentpress_tools: Dict[str, Any]
    is_active: bool
    status: str
    created_at: str
    updated_at: str
    created_by: str
    model: Optional[str] = None
    change_description: Optional[str] = None
    previous_version_id: Optional[str] = None


@dataclass
class VersionComparisonResponse:
    version1: VersionResponse
    version2: VersionResponse
    differences: List[Dict[str, Any]]


# Use shared serialization utilities
to_dict = base_to_dict
from_dict = base_from_dict


class VersionsClient(BaseAPIClient):
    """SDK client for NeuroCluster Agent Versions API"""

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the Versions API client

        Args:
            base_url: Base URL of the API (e.g., "https://api.neurocluster.com/api")
            auth_token: JWT token for authentication
            custom_headers: Additional headers to include in all requests
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, auth_token, custom_headers, timeout)

    async def get_versions(self, agent_id: str) -> List[VersionResponse]:
        """
        Get all versions for an agent

        Args:
            agent_id: Agent identifier

        Returns:
            List of VersionResponse objects
        """
        response = await self._request_with_retry("GET", f"/agents/{agent_id}/versions")
        data = self._handle_response(response)
        return [from_dict(VersionResponse, version) for version in data]

    async def get_version(self, agent_id: str, version_id: str) -> VersionResponse:
        """
        Get a specific version by ID

        Args:
            agent_id: Agent identifier
            version_id: Version identifier

        Returns:
            VersionResponse with version details
        """
        response = await self._request_with_retry("GET", f"/agents/{agent_id}/versions/{version_id}")
        data = self._handle_response(response)
        return from_dict(VersionResponse, data)

    async def create_version(
        self, agent_id: str, request: CreateVersionRequest
    ) -> VersionResponse:
        """
        Create a new version for an agent

        Args:
            agent_id: Agent identifier
            request: CreateVersionRequest with version details

        Returns:
            Created VersionResponse
        """
        response = await self._request_with_retry(
            "POST", f"/agents/{agent_id}/versions", json=to_dict(request)
        )
        data = self._handle_response(response)
        return from_dict(VersionResponse, data)

    async def activate_version(self, agent_id: str, version_id: str) -> Dict[str, str]:
        """
        Activate a version (make it the active version)

        Args:
            agent_id: Agent identifier
            version_id: Version identifier

        Returns:
            Success message
        """
        response = await self._request_with_retry(
            "PUT", f"/agents/{agent_id}/versions/{version_id}/activate"
        )
        data = self._handle_response(response)
        return data

    async def rollback_to_version(
        self, agent_id: str, version_id: str
    ) -> VersionResponse:
        """
        Rollback to a specific version (creates a new version based on the specified version)

        Args:
            agent_id: Agent identifier
            version_id: Version identifier to rollback to

        Returns:
            New VersionResponse created from rollback
        """
        response = await self._request_with_retry(
            "POST", f"/agents/{agent_id}/versions/{version_id}/rollback"
        )
        data = self._handle_response(response)
        return from_dict(VersionResponse, data)

    async def compare_versions(
        self, agent_id: str, version1_id: str, version2_id: str
    ) -> VersionComparisonResponse:
        """
        Compare two versions

        Args:
            agent_id: Agent identifier
            version1_id: First version identifier
            version2_id: Second version identifier

        Returns:
            VersionComparisonResponse with differences
        """
        response = await self._request_with_retry(
            "GET", f"/agents/{agent_id}/versions/{version1_id}/compare/{version2_id}"
        )
        data = self._handle_response(response)
        version1 = from_dict(VersionResponse, data["version1"])
        version2 = from_dict(VersionResponse, data["version2"])
        return VersionComparisonResponse(
            version1=version1, version2=version2, differences=data["differences"]
        )

    async def update_version_details(
        self, agent_id: str, version_id: str, request: UpdateVersionDetailsRequest
    ) -> VersionResponse:
        """
        Update version details (name and description)

        Args:
            agent_id: Agent identifier
            version_id: Version identifier
            request: UpdateVersionDetailsRequest with updated fields

        Returns:
            Updated VersionResponse
        """
        response = await self._request_with_retry(
            "PUT", f"/agents/{agent_id}/versions/{version_id}/details", json=to_dict(request)
        )
        data = self._handle_response(response)
        return from_dict(VersionResponse, data)


# Convenience function to create a client instance
def create_versions_client(
    base_url: str,
    auth_token: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
) -> VersionsClient:
    """
    Create a VersionsClient instance

    Args:
        base_url: Base URL of the API
        auth_token: JWT token for authentication
        custom_headers: Additional headers to include in all requests
        timeout: Request timeout in seconds

    Returns:
        VersionsClient instance
    """
    return VersionsClient(
        base_url=base_url,
        auth_token=auth_token,
        custom_headers=custom_headers,
        timeout=timeout,
    )

