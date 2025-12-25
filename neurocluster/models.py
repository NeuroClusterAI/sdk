from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any, List
from enum import Enum

from .types import ToolCall, MessageMetadata, AgentRunError


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ContentObject:
    role: Role  # "user" | "assistant" | "system"
    content: Optional[str]
    tool_calls: Optional[List[ToolCall]] = None


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    STATUS = "status"
    ASSISTANT_RESPONSE_END = "assistant_response_end"


@dataclass
class BaseMessage:
    message_id: str
    thread_id: str
    type: MessageType  # "user" | "assistant" | "tool" | "status" | "assistant_response_end"
    is_llm_message: bool
    metadata: MessageMetadata
    created_at: str
    updated_at: str


@dataclass
class UserMessage(BaseMessage):
    type: MessageType = field(init=False, default=MessageType.USER)
    content: str  # JSON string of ContentObject


@dataclass
class AssistantMessage(BaseMessage):
    type: MessageType = field(init=False, default=MessageType.ASSISTANT)
    content: ContentObject


@dataclass
class ToolResultMessage(BaseMessage):
    type: MessageType = field(init=False, default=MessageType.TOOL)
    content: Dict[
        str, Union[str, Any]
    ]  # role: "user", content: JSON string of ToolExecutionResult


@dataclass
class StatusMessage(BaseMessage):
    type: MessageType = field(init=False, default=MessageType.STATUS)
    content: Dict[str, Any]  # status_type and other fields


@dataclass
class AssistantResponseEndMessage(BaseMessage):
    type: MessageType = field(init=False, default=MessageType.ASSISTANT_RESPONSE_END)
    content: Dict[str, Any]  # model, usage, etc.


ChatMessage = Union[
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    StatusMessage,
    AssistantResponseEndMessage,
]


@dataclass
class AgentRun:
    id: str
    thread_id: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[AgentRunError]
    created_at: str
    updated_at: str
