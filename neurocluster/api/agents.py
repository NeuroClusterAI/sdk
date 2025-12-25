import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import json

from ..tools import AgentPressTools
from .base_client import BaseAPIClient
from .serialization import to_dict as base_to_dict, from_dict as base_from_dict
from .constants import APIHeaders


@dataclass
class MCPConfig:
    url: str


@dataclass
class CustomMCP:
    name: str
    type: str  # sse, http, etc
    config: MCPConfig
    enabled_tools: List[str]


@dataclass
class AgentPress_ToolConfig:
    enabled: bool
    description: str


@dataclass
class AgentCreateRequest:
    name: str
    system_prompt: str
    description: Optional[str] = None
    configured_mcps: Optional[List[CustomMCP]] = None
    custom_mcps: Optional[List[CustomMCP]] = None
    agentpress_tools: Optional[Dict[AgentPressTools, AgentPress_ToolConfig]] = None
    is_default: bool = False
    profile_image_url: Optional[str] = None
    icon_name: Optional[str] = None
    icon_color: Optional[str] = None
    icon_background: Optional[str] = None


@dataclass
class AgentUpdateRequest:
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    configured_mcps: Optional[List[CustomMCP]] = None
    custom_mcps: Optional[List[CustomMCP]] = None
    agentpress_tools: Optional[Dict[AgentPressTools, AgentPress_ToolConfig]] = None
    is_default: Optional[bool] = None
    profile_image_url: Optional[str] = None
    icon_name: Optional[str] = None
    icon_color: Optional[str] = None
    icon_background: Optional[str] = None
    replace_mcps: Optional[bool] = None


@dataclass
class PipedreamToolsUpdateRequest:
    enabled_tools: List[str]


@dataclass
class CustomMCPToolsUpdateRequest:
    url: str
    type: str
    enabled_tools: List[str]


# Response Models
@dataclass
class AgentVersionResponse:
    version_id: str
    agent_id: str
    version_number: int
    version_name: str
    system_prompt: str
    configured_mcps: List[CustomMCP]
    custom_mcps: List[CustomMCP]
    agentpress_tools: Dict[AgentPressTools, AgentPress_ToolConfig]
    is_active: bool
    created_at: str
    updated_at: str
    model: Optional[str] = None
    created_by: Optional[str] = None


@dataclass
class AgentResponse:
    agent_id: str
    account_id: str
    name: str
    system_prompt: str
    configured_mcps: List[CustomMCP]
    custom_mcps: List[CustomMCP]
    agentpress_tools: Dict[AgentPressTools, AgentPress_ToolConfig]
    is_default: bool
    created_at: str
    description: Optional[str] = None
    updated_at: Optional[str] = None
    is_public: Optional[bool] = False
    marketplace_published_at: Optional[str] = None
    download_count: Optional[int] = 0
    tags: Optional[List[str]] = None
    current_version_id: Optional[str] = None
    version_count: Optional[int] = 1
    current_version: Optional[AgentVersionResponse] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PaginationInfo:
    page: int
    limit: int
    total: int
    pages: int


@dataclass
class AgentsResponse:
    agents: List[AgentResponse]
    pagination: PaginationInfo


@dataclass
class AgentTool:
    name: str
    enabled: bool
    server: Optional[str] = None  # For MCP tools
    description: Optional[str] = None


@dataclass
class AgentToolsResponse:
    agentpress_tools: List[AgentTool]
    mcp_tools: List[AgentTool]


@dataclass
class PipedreamTool:
    name: str
    description: str
    enabled: bool


@dataclass
class PipedreamToolsResponse:
    profile_id: str
    app_name: str
    profile_name: str
    tools: List[PipedreamTool]
    has_mcp_config: bool
    error: Optional[str] = None


@dataclass
class CustomMCPTool:
    name: str
    description: str
    enabled: bool


@dataclass
class CustomMCPToolsResponse:
    tools: List[CustomMCPTool]
    has_mcp_config: bool
    server_type: str
    server_url: str


@dataclass
class PipedreamToolsUpdateResponse:
    success: bool
    enabled_tools: List[str]
    total_tools: int
    version_name: Optional[str] = None


@dataclass
class CustomMCPToolsUpdateResponse:
    success: bool
    enabled_tools: List[str]
    total_tools: int


@dataclass
class AgentBuilderChatMessage:
    message_id: str
    thread_id: str
    type: str
    is_llm_message: bool
    content: str
    created_at: str


@dataclass
class AgentBuilderChatHistoryResponse:
    messages: List[AgentBuilderChatMessage]
    thread_id: Optional[str]


@dataclass
class DeleteAgentResponse:
    message: str


@dataclass
class AgentIconGenerationRequest:
    name: str
    description: Optional[str] = None


@dataclass
class AgentIconGenerationResponse:
    icon_name: str
    icon_color: str
    icon_background: str


@dataclass
class AgentExportData:
    name: str
    system_prompt: str
    agentpress_tools: Dict[str, Any]
    configured_mcps: List[Dict[str, Any]]
    custom_mcps: List[Dict[str, Any]]
    exported_at: str
    description: Optional[str] = None
    profile_image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    export_version: str = "1.1"
    exported_by: Optional[str] = None


@dataclass
class JsonAnalysisRequest:
    json_data: Dict[str, Any]


@dataclass
class JsonAnalysisResponse:
    requires_setup: bool
    missing_regular_credentials: List[Dict[str, Any]]
    missing_custom_configs: List[Dict[str, Any]]
    agent_info: Dict[str, Any]


@dataclass
class JsonImportRequestModel:
    json_data: Dict[str, Any]
    instance_name: Optional[str] = None
    custom_system_prompt: Optional[str] = None
    profile_mappings: Optional[Dict[str, str]] = None
    custom_mcp_configs: Optional[Dict[str, Dict[str, Any]]] = None


@dataclass
class JsonImportResponse:
    status: str
    instance_id: Optional[str] = None
    name: Optional[str] = None
    missing_regular_credentials: Optional[List[Dict[str, Any]]] = None
    missing_custom_configs: Optional[List[Dict[str, Any]]] = None
    agent_info: Optional[Dict[str, Any]] = None


# Use shared serialization utilities
to_dict = base_to_dict
from_dict = base_from_dict

# Import registry decorator
from .serialization import register_from_dict


# Register custom handlers for agents-specific types
@register_from_dict(AgentsResponse)
def _from_dict_agents_response(data: Dict[str, Any]) -> AgentsResponse:
    """Custom handler for AgentsResponse with nested agents list."""
    agents = [from_dict(AgentResponse, agent) for agent in data.get("agents", [])]
    pagination = from_dict(PaginationInfo, data.get("pagination", {}))
    return AgentsResponse(agents=agents, pagination=pagination)


@register_from_dict(AgentResponse)
def _from_dict_agent_response(data: Dict[str, Any]) -> AgentResponse:
    """Custom handler for AgentResponse with nested version and MCP configs."""
    current_version = None
    if data.get("current_version"):
        current_version = from_dict(AgentVersionResponse, data["current_version"])

    # Handle configured_mcps conversion
    configured_mcps = []
    if data.get("configured_mcps"):
        configured_mcps = [from_dict(CustomMCP, mcp) for mcp in data["configured_mcps"]]

    # Handle custom_mcps conversion
    custom_mcps = []
    if data.get("custom_mcps"):
        custom_mcps = [from_dict(CustomMCP, mcp) for mcp in data["custom_mcps"]]

    # Create a copy of data without nested objects for the main object
    agent_data = {
        k: v for k, v in data.items() if k not in ["current_version", "configured_mcps", "custom_mcps"]
    }
    agent_data["current_version"] = current_version
    agent_data["configured_mcps"] = configured_mcps
    agent_data["custom_mcps"] = custom_mcps
    agent_data["tags"] = agent_data.get("tags", [])

    return AgentResponse(
        **{k: v for k, v in agent_data.items() if k in AgentResponse.__dataclass_fields__}
    )


@register_from_dict(AgentToolsResponse)
def _from_dict_agent_tools_response(data: Dict[str, Any]) -> AgentToolsResponse:
    """Custom handler for AgentToolsResponse with nested tool lists."""
    agentpress_tools = [
        from_dict(AgentTool, tool) for tool in data.get("agentpress_tools", [])
    ]
    mcp_tools = [from_dict(AgentTool, tool) for tool in data.get("mcp_tools", [])]
    return AgentToolsResponse(agentpress_tools=agentpress_tools, mcp_tools=mcp_tools)


@register_from_dict(PipedreamToolsResponse)
def _from_dict_pipedream_tools_response(data: Dict[str, Any]) -> PipedreamToolsResponse:
    """Custom handler for PipedreamToolsResponse with nested tools."""
    tools = [from_dict(PipedreamTool, tool) for tool in data.get("tools", [])]
    return PipedreamToolsResponse(
        profile_id=data["profile_id"],
        app_name=data["app_name"],
        profile_name=data["profile_name"],
        tools=tools,
        has_mcp_config=data["has_mcp_config"],
        error=data.get("error"),
    )


@register_from_dict(CustomMCPToolsResponse)
def _from_dict_custom_mcp_tools_response(data: Dict[str, Any]) -> CustomMCPToolsResponse:
    """Custom handler for CustomMCPToolsResponse with nested tools."""
    tools = [from_dict(CustomMCPTool, tool) for tool in data.get("tools", [])]
    return CustomMCPToolsResponse(
        tools=tools,
        has_mcp_config=data["has_mcp_config"],
        server_type=data["server_type"],
        server_url=data["server_url"],
    )


@register_from_dict(AgentBuilderChatHistoryResponse)
def _from_dict_agent_builder_chat_history(data: Dict[str, Any]) -> AgentBuilderChatHistoryResponse:
    """Custom handler for AgentBuilderChatHistoryResponse with nested messages."""
    messages = [
        from_dict(AgentBuilderChatMessage, msg) for msg in data.get("messages", [])
    ]
    return AgentBuilderChatHistoryResponse(messages=messages, thread_id=data.get("thread_id"))


@register_from_dict(CustomMCP)
def _from_dict_custom_mcp(data: Dict[str, Any]) -> CustomMCP:
    """Custom handler for CustomMCP with nested MCPConfig."""
    # Handle nested MCPConfig conversion
    config_data = data.get("config", {})
    # Ensure we always have a valid MCPConfig object
    if isinstance(config_data, dict):
        # Provide default url if missing
        if "url" not in config_data:
            config_data["url"] = ""
        config = from_dict(MCPConfig, config_data)
    else:
        # Fallback to empty MCPConfig if config is not a dict
        config = MCPConfig(url="")

    # Create a copy without config for the main object
    mcp_data = {k: v for k, v in data.items() if k != "config"}
    mcp_data["config"] = config

    return CustomMCP(
        **{k: v for k, v in mcp_data.items() if k in CustomMCP.__dataclass_fields__}
    )


class AgentsClient(BaseAPIClient):
    """SDK client for NeuroCluster Agents API with httpx client supporting custom headers"""
    
    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the Agents API client

        Args:
            base_url: Base URL of the API (e.g., "https://api.neurocluster.com/api")
            auth_token: JWT token for authentication
            custom_headers: Additional headers to include in all requests
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, auth_token, custom_headers, timeout)

    # Agents CRUD operations

    async def get_agents(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        has_default: Optional[bool] = None,
        has_mcp_tools: Optional[bool] = None,
        has_agentpress_tools: Optional[bool] = None,
        tools: Optional[str] = None,
    ) -> AgentsResponse:
        """
        Get agents with pagination, search, sort, and filter support

        Args:
            page: Page number (1-based)
            limit: Number of items per page (1-100)
            search: Search in name and description
            sort_by: Sort field (name, created_at, updated_at, tools_count)
            sort_order: Sort order (asc, desc)
            has_default: Filter by default agents
            has_mcp_tools: Filter by agents with MCP tools
            has_agentpress_tools: Filter by agents with AgentPress tools
            tools: Comma-separated list of tools to filter by

        Returns:
            AgentsResponse containing agents list and pagination info
        """
        params = {
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        # Add optional parameters if provided
        if search:
            params["search"] = search
        if has_default is not None:
            params["has_default"] = has_default
        if has_mcp_tools is not None:
            params["has_mcp_tools"] = has_mcp_tools
        if has_agentpress_tools is not None:
            params["has_agentpress_tools"] = has_agentpress_tools
        if tools:
            params["tools"] = tools

        response = await self._request_with_retry("GET", "/agents", params=params)
        data = self._handle_response(response)
        return from_dict(AgentsResponse, data)

    async def get_agent(self, agent_id: str) -> AgentResponse:
        """
        Get a specific agent by ID

        Args:
            agent_id: Agent identifier

        Returns:
            AgentResponse with current version information
        """
        response = await self._request_with_retry("GET", f"/agents/{agent_id}")
        data = self._handle_response(response)
        return from_dict(AgentResponse, data)

    async def create_agent(self, request: AgentCreateRequest) -> AgentResponse:
        """
        Create a new agent

        Args:
            request: AgentCreateRequest with agent details

        Returns:
            Created AgentResponse
        """
        response = await self._request_with_retry("POST", "/agents", json=to_dict(request))
        data = self._handle_response(response)
        return from_dict(AgentResponse, data)

    async def update_agent(
        self, agent_id: str, request: AgentUpdateRequest
    ) -> AgentResponse:
        """
        Update an existing agent

        Args:
            agent_id: Agent identifier
            request: AgentUpdateRequest with updated fields

        Returns:
            Updated AgentResponse
        """
        response = await self._request_with_retry("PUT", f"/agents/{agent_id}", json=to_dict(request))
        data = self._handle_response(response)
        return from_dict(AgentResponse, data)

    async def delete_agent(self, agent_id: str) -> DeleteAgentResponse:
        """
        Delete an agent

        Args:
            agent_id: Agent identifier

        Returns:
            DeleteAgentResponse with confirmation message
        """
        response = await self._request_with_retry("DELETE", f"/agents/{agent_id}")
        data = self._handle_response(response)
        return from_dict(DeleteAgentResponse, data)

    # Agent tools and integrations

    async def get_agent_tools(self, agent_id: str) -> AgentToolsResponse:
        """
        Get enabled tools for an agent

        Args:
            agent_id: Agent identifier

        Returns:
            AgentToolsResponse containing agentpress_tools and mcp_tools lists
        """
        response = await self._request_with_retry("GET", f"/agents/{agent_id}/tools")
        data = self._handle_response(response)
        return from_dict(AgentToolsResponse, data)

    async def get_pipedream_tools(
        self, agent_id: str, profile_id: str, version: Optional[str] = None
    ) -> PipedreamToolsResponse:
        """
        Get Pipedream tools for an agent profile

        Args:
            agent_id: Agent identifier
            profile_id: Pipedream profile identifier
            version: Optional version ID to get tools from specific version

        Returns:
            PipedreamToolsResponse containing profile info and available tools
        """
        params = {}
        if version:
            params["version"] = version

        response = await self._request_with_retry(
            "GET", f"/agents/{agent_id}/pipedream-tools/{profile_id}", params=params
        )
        data = self._handle_response(response)
        return from_dict(PipedreamToolsResponse, data)

    async def update_pipedream_tools(
        self, agent_id: str, profile_id: str, request: PipedreamToolsUpdateRequest
    ) -> PipedreamToolsUpdateResponse:
        """
        Update Pipedream tools for an agent profile

        Args:
            agent_id: Agent identifier
            profile_id: Pipedream profile identifier
            request: PipedreamToolsUpdateRequest with enabled tools

        Returns:
            PipedreamToolsUpdateResponse with update result
        """
        response = await self._request_with_retry(
            "PUT", f"/agents/{agent_id}/pipedream-tools/{profile_id}", json=to_dict(request)
        )
        data = self._handle_response(response)
        return from_dict(PipedreamToolsUpdateResponse, data)

    async def get_custom_mcp_tools(
        self,
        agent_id: str,
        mcp_url: str,
        mcp_type: str = "sse",
        headers: Optional[Dict[str, str]] = None,
    ) -> CustomMCPToolsResponse:
        """
        Get custom MCP tools for an agent

        Args:
            agent_id: Agent identifier
            mcp_url: MCP server URL
            mcp_type: MCP server type (default: "sse")
            headers: Optional additional headers for MCP server

        Returns:
            CustomMCPToolsResponse containing available tools and server info
        """
        request_headers = {APIHeaders.MCP_URL: mcp_url, APIHeaders.MCP_TYPE: mcp_type}

        if headers:
            request_headers[APIHeaders.MCP_HEADERS] = json.dumps(headers)

        response = await self._request_with_retry(
            "GET", f"/agents/{agent_id}/custom-mcp-tools", headers=request_headers
        )
        data = self._handle_response(response)
        return from_dict(CustomMCPToolsResponse, data)

    async def update_custom_mcp_tools(
        self, agent_id: str, request: CustomMCPToolsUpdateRequest
    ) -> CustomMCPToolsUpdateResponse:
        """
        Update custom MCP tools for an agent

        Args:
            agent_id: Agent identifier
            request: CustomMCPToolsUpdateRequest with server details and enabled tools

        Returns:
            CustomMCPToolsUpdateResponse with update result
        """
        response = await self._request_with_retry(
            "POST", f"/agents/{agent_id}/custom-mcp-tools", json=to_dict(request)
        )
        data = self._handle_response(response)
        return from_dict(CustomMCPToolsUpdateResponse, data)

    # Agent builder functionality

    async def get_agent_builder_chat_history(
        self, agent_id: str
    ) -> AgentBuilderChatHistoryResponse:
        """
        Get chat history for agent builder sessions

        Args:
            agent_id: Agent identifier

        Returns:
            AgentBuilderChatHistoryResponse containing messages and thread_id
        """
        response = await self._request_with_retry("GET", f"/agents/{agent_id}/builder-chat-history")
        data = self._handle_response(response)
        return from_dict(AgentBuilderChatHistoryResponse, data)

    async def generate_icon(
        self, request: AgentIconGenerationRequest
    ) -> AgentIconGenerationResponse:
        """
        Generate an appropriate icon and colors for an agent based on its name and description

        Args:
            request: AgentIconGenerationRequest with agent name and optional description

        Returns:
            AgentIconGenerationResponse with generated icon_name, icon_color, and icon_background
        """
        response = await self._request_with_retry("POST", "/agents/generate-icon", json=to_dict(request))
        data = self._handle_response(response)
        return from_dict(AgentIconGenerationResponse, data)

    # Export/Import functionality

    async def export_agent(self, agent_id: str) -> AgentExportData:
        """
        Export an agent configuration as JSON

        Args:
            agent_id: Agent identifier

        Returns:
            AgentExportData with agent configuration
        """
        response = await self._request_with_retry("GET", f"/agents/{agent_id}/export")
        data = self._handle_response(response)
        return from_dict(AgentExportData, data)

    async def analyze_json(
        self, request: JsonAnalysisRequest
    ) -> JsonAnalysisResponse:
        """
        Analyze imported JSON to determine required credentials and configurations

        Args:
            request: JsonAnalysisRequest with JSON data to analyze

        Returns:
            JsonAnalysisResponse with analysis results and missing requirements
        """
        response = await self._request_with_retry("POST", "/agents/json/analyze", json=to_dict(request))
        data = self._handle_response(response)
        return from_dict(JsonAnalysisResponse, data)

    async def import_json(
        self, request: JsonImportRequestModel
    ) -> JsonImportResponse:
        """
        Import an agent from JSON configuration

        Args:
            request: JsonImportRequestModel with JSON data and import options

        Returns:
            JsonImportResponse with import status and agent information
        """
        response = await self._request_with_retry("POST", "/agents/json/import", json=to_dict(request))
        data = self._handle_response(response)
        return from_dict(JsonImportResponse, data)


# Convenience function to create a client instance
def create_agents_client(
    base_url: str,
    auth_token: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
) -> AgentsClient:
    """
    Create an AgentsClient instance

    Args:
        base_url: Base URL of the API
        auth_token: JWT token for authentication
        custom_headers: Additional headers to include in all requests
        timeout: Request timeout in seconds

    Returns:
        AgentsClient instance
    """
    return AgentsClient(
        base_url=base_url,
        auth_token=auth_token,
        custom_headers=custom_headers,
        timeout=timeout,
    )


