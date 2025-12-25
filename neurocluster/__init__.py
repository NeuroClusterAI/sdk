"""
NeuroCluster Python SDK.

This package provides a small async client for the NeuroCluster API, plus helpers
for MCP tool integration.
"""

from .neurocluster import NeuroCluster
from .tools import AgentPressTools, MCPTools
from .stream_parser import (
    StreamParser,
    StreamEvent,
    StatusEvent,
    AssistantChunkEvent,
    AssistantMessageEvent,
    ToolUseDetectedEvent,
    ToolInvocationEvent,
    ToolUseWaitingEvent,
    ToolResultEvent,
    StreamStartEvent,
    StreamEndEvent,
    ParseErrorEvent,
)
from .api.rate_limit import RateLimiter, AdaptiveRateLimiter

# Backwards compatibility:
# Some internal code (and older docs) use `from neurocluster import neurocluster`
# and expect a module-like object with these attributes.
import sys
from types import ModuleType

neurocluster = ModuleType("neurocluster")
neurocluster.NeuroCluster = NeuroCluster
neurocluster.MCPTools = MCPTools
neurocluster.AgentPressTools = AgentPressTools

# Also expose it as a submodule to support `import neurocluster.neurocluster`
sys.modules["neurocluster.neurocluster"] = neurocluster

__all__ = [
    "NeuroCluster",
    "AgentPressTools",
    "MCPTools",
    "neurocluster",
    # Stream parsing
    "StreamParser",
    "StreamEvent",
    "StatusEvent",
    "AssistantChunkEvent",
    "AssistantMessageEvent",
    "ToolUseDetectedEvent",
    "ToolInvocationEvent",
    "ToolUseWaitingEvent",
    "ToolResultEvent",
    "StreamStartEvent",
    "StreamEndEvent",
    "ParseErrorEvent",
    # Rate limiting
    "RateLimiter",
    "AdaptiveRateLimiter",
]

