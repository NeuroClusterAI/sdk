"""Type definitions for better type safety."""

from typing import TypedDict, List, Optional, Dict, Any, Union


class ToolCall(TypedDict, total=False):
    """Tool call structure."""
    id: str
    type: str
    function: Dict[str, Any]
    name: Optional[str]
    arguments: Optional[Dict[str, Any]]


class ToolExecutionResult(TypedDict, total=False):
    """Tool execution result structure."""
    tool_execution: Dict[str, Any]
    success: bool
    output: Dict[str, Any]
    error: Optional[Dict[str, Any]]


class MessageMetadata(TypedDict, total=False):
    """Message metadata structure."""
    pass  # Can be extended with specific metadata fields


class AgentRunError(TypedDict, total=False):
    """Agent run error structure."""
    message: str
    code: Optional[str]
    details: Optional[Dict[str, Any]]


class StatusContent(TypedDict, total=False):
    """Status message content structure."""
    status_type: str
    message: Optional[str]
    finish_reason: Optional[str]


class AssistantResponseEndContent(TypedDict, total=False):
    """Assistant response end content structure."""
    model: str
    usage: Optional[Dict[str, Any]]
    finish_reason: Optional[str]


# Union type for message content
MessageContent = Union[str, Dict[str, Any], ToolExecutionResult, StatusContent, AssistantResponseEndContent]

