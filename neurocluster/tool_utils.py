"""Utility functions for tool processing in the SDK."""

from typing import Dict, List, Tuple, Any
from .tools import AgentPressTools, MCPTools, NeuroClusterTools
from .api.agents import (
    AgentPress_ToolConfig,
    CustomMCP,
    MCPConfig,
)


def process_mcp_tools(
    mcp_tools: List[NeuroClusterTools],
    allowed_tools: List[str] | None = None,
) -> Tuple[Dict[AgentPressTools, AgentPress_ToolConfig], List[CustomMCP]]:
    """
    Process MCP tools into agentpress_tools and custom_mcps configurations.
    
    This function consolidates the common tool processing logic used during
    agent creation and updates.
    
    Args:
        mcp_tools: List of tools to process (AgentPressTools or MCPTools)
        allowed_tools: Optional list of tool IDs/names to enable. If provided,
                      only these tools will be enabled.
    
    Returns:
        Tuple of (agentpress_tools dict, custom_mcps list)
        
    Raises:
        ValueError: If an unknown tool type is provided
    """
    agentpress_tools: Dict[AgentPressTools, AgentPress_ToolConfig] = {}
    custom_mcps: List[CustomMCP] = []
    
    for tool in mcp_tools:
        if isinstance(tool, AgentPressTools):
            # AgentPressTools is a str Enum; .value is the actual tool id
            # (e.g. "sb_files_tool"), whereas .name is the enum member name.
            is_enabled = tool.value in allowed_tools if allowed_tools else True
            agentpress_tools[tool] = AgentPress_ToolConfig(
                enabled=is_enabled, description=tool.get_description()
            )
        elif isinstance(tool, MCPTools):
            # allowed_tools refers to individual tool names (not MCP server name).
            enabled_tools = (
                [t for t in tool.enabled_tools if t in allowed_tools]
                if allowed_tools
                else tool.enabled_tools
            )
            custom_mcps.append(
                CustomMCP(
                    name=tool.name,
                    type=tool.type,
                    config=MCPConfig(url=tool.url),
                    enabled_tools=enabled_tools,
                )
            )
        else:
            raise ValueError(f"Unknown tool type: {type(tool)}")
    
    return agentpress_tools, custom_mcps


def filter_existing_tools(
    agentpress_tools: Dict[Any, Any],
    custom_mcps: List[CustomMCP],
    allowed_tools: List[str],
) -> None:
    """
    Filter existing tools based on allowed_tools list.
    
    This function modifies the provided dicts/lists in place to disable
    tools that are not in the allowed_tools list.
    
    Args:
        agentpress_tools: Dict of agentpress tool configurations (modified in place)
        custom_mcps: List of custom MCP configurations (modified in place)
        allowed_tools: List of tool IDs/names to keep enabled
    """
    # Filter agentpress tools - may come from API as dict keyed by strings
    for tool_key in agentpress_tools:
        tool_id = tool_key.value if isinstance(tool_key, AgentPressTools) else str(tool_key)
        if tool_id not in allowed_tools:
            cfg = agentpress_tools[tool_key]
            if hasattr(cfg, "enabled"):
                cfg.enabled = False
            elif isinstance(cfg, dict):
                cfg["enabled"] = False
    
    # Filter MCP enabled tools down to those explicitly allowed
    for mcp in custom_mcps:
        mcp.enabled_tools = [t for t in mcp.enabled_tools if t in allowed_tools]

