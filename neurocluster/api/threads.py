from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
import httpx
from datetime import datetime

# Import from shared models
from ..models import (
    Role,
    MessageType,
    BaseMessage,
    ChatMessage,
    AgentRun,
    ContentObject,
)
from ..types import MessageContent
from .base_client import BaseAPIClient
from .serialization import to_dict, from_dict as base_from_dict


@dataclass
class MessageCreateRequest:
    content: str
    type: str = "user"  # Should be MessageType value
    is_llm_message: bool = True

    def __post_init__(self):
        """Validate that type is a valid MessageType"""
        try:
            MessageType(self.type)
        except ValueError:
            raise ValueError(
                f"Invalid message type: {self.type}. Must be one of {[t.value for t in MessageType]}"
            )

    @classmethod
    def create_user_message(cls, content: str) -> "MessageCreateRequest":
        """Create a user message"""
        return cls(content=content, type=MessageType.USER.value, is_llm_message=True)

    @classmethod
    def create_system_message(cls, content: str) -> "MessageCreateRequest":
        """Create a system message"""
        return cls(content=content, type="system", is_llm_message=False)


@dataclass
class AgentStartRequest:
    model_name: Optional[str] = None
    enable_thinking: Optional[bool] = False
    reasoning_effort: Optional[str] = "low"
    stream: Optional[bool] = True
    enable_context_manager: Optional[bool] = False
    enable_prompt_caching: Optional[bool] = True
    agent_id: Optional[str] = None


@dataclass
class ProjectData:
    project_id: str
    name: str
    description: str
    account_id: str
    sandbox: Dict[str, Any]
    is_public: bool
    created_at: str
    updated_at: str


@dataclass
class AgentRunApiResponse(AgentRun):
    """Extended AgentRun with additional API fields"""

    agent_id: Optional[str] = None
    agent_version_id: Optional[str] = None


@dataclass
class Thread:
    thread_id: str
    account_id: str
    project_id: Optional[str]
    metadata: Dict[str, Any]
    is_public: bool
    created_at: str
    updated_at: str
    project: Optional[ProjectData] = None
    message_count: Optional[int] = None
    recent_agent_runs: Optional[List[AgentRunApiResponse]] = None


@dataclass
class Message:
    message_id: str
    thread_id: str
    type: str  # Will map to MessageType enum values
    is_llm_message: bool
    content: MessageContent  # Can be string, dict, or ContentObject
    created_at: str
    updated_at: str
    agent_id: str
    agent_version_id: str
    metadata: Dict[str, Any]

    @property
    def message_type(self) -> MessageType:
        """Get the MessageType enum value"""
        try:
            return MessageType(self.type)
        except ValueError:
            # Fallback for unknown message types
            return MessageType.USER

    @property
    def is_user_message(self) -> bool:
        """Check if this is a user message"""
        return self.message_type == MessageType.USER

    @property
    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message"""
        return self.message_type == MessageType.ASSISTANT

    def get_content_as_string(self) -> str:
        """Get content as string, handling different content types"""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, dict):
            return self.content.get("content", str(self.content))
        else:
            return str(self.content)


@dataclass
class PaginationInfo:
    page: int
    limit: int
    total: int
    pages: int


@dataclass
class ThreadsResponse:
    threads: List[Thread]
    pagination: PaginationInfo


@dataclass
class MessagesResponse:
    messages: List[Message]


@dataclass
class CreateThreadResponse:
    thread_id: str
    project_id: str


@dataclass
class AgentResponse:
    agent_id: str
    account_id: str
    name: str
    description: Optional[str]
    system_prompt: str
    configured_mcps: List[Dict[str, Any]]
    custom_mcps: List[Dict[str, Any]]
    agentpress_tools: Dict[str, Any]
    is_default: bool
    is_public: Optional[bool]
    marketplace_published_at: Optional[str]
    download_count: Optional[int]
    tags: Optional[List[str]]
    created_at: str
    updated_at: Optional[str]
    current_version_id: Optional[str]
    version_count: Optional[int]
    current_version: Optional[Any]
    metadata: Optional[Dict[str, Any]]


@dataclass
class ThreadAgentResponse:
    agent: Optional[AgentResponse]
    source: str  # "thread", "default", "none", "missing"
    message: str


@dataclass
class AgentStartResponse:
    agent_run_id: str
    status: str


@dataclass
class AgentRunResponse:
    id: str
    threadId: str
    status: str
    startedAt: Optional[str]
    completedAt: Optional[str]
    error: Optional[str]


@dataclass
class AgentRunsResponse:
    agent_runs: List[Dict[str, Any]]


# Use shared serialization utilities
# Note: threads.py needs to preserve None values in some cases, use to_dict(obj, exclude_none=False)
from_dict = base_from_dict


class ThreadsClient(BaseAPIClient):
    """Client for interacting with threads APIs."""

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: float = 120.0,  # Default timeout is longer for threads
    ):
        """Initialize the threads client.

        Args:
            base_url: The base URL for the API
            auth_token: Optional authentication token
            custom_headers: Optional custom headers to include in requests
            timeout: Request timeout in seconds (default: 120.0)
        """
        super().__init__(base_url, auth_token, custom_headers, timeout)

    async def get_threads(
        self,
        page: int = 1,
        limit: int = 1000,
    ) -> ThreadsResponse:
        """Get all threads for the current user with associated project data.

        Args:
            page: Page number (1-based)
            limit: Number of items per page (max 1000)

        Returns:
            ThreadsResponse containing paginated threads
        """
        params = {
            "page": page,
            "limit": limit,
        }

        response = await self._request_with_retry("GET", "/threads", params=params)
        data = self._handle_response(response)

        # Convert threads data
        threads = []
        for thread_data in data["threads"]:
            project_data = None
            if thread_data.get("project"):
                project_data = from_dict(ProjectData, thread_data["project"])

            agent_runs_data = []
            if thread_data.get("recent_agent_runs"):
                agent_runs_data = [
                    from_dict(AgentRunApiResponse, run_data)
                    for run_data in thread_data["recent_agent_runs"]
                ]

            thread = from_dict(
                Thread,
                {
                    **thread_data,
                    "project": project_data,
                    "recent_agent_runs": agent_runs_data,
                },
            )
            threads.append(thread)

        pagination = from_dict(PaginationInfo, data["pagination"])

        return ThreadsResponse(threads=threads, pagination=pagination)

    async def get_thread(self, thread_id: str) -> Thread:
        """Get a specific thread by ID with complete related data.

        Args:
            thread_id: The thread ID

        Returns:
            Thread with complete data including project, message count, and recent agent runs
        """
        response = await self._request_with_retry("GET", f"/threads/{thread_id}")
        data = self._handle_response(response)

        # Handle nested project data
        project_data = None
        if data.get("project"):
            project_data = from_dict(ProjectData, data["project"])

        # Handle recent agent runs
        agent_runs_data = []
        if data.get("recent_agent_runs"):
            agent_runs_data = [
                from_dict(AgentRunApiResponse, run_data)
                for run_data in data["recent_agent_runs"]
            ]

        return from_dict(
            Thread,
            {**data, "project": project_data, "recent_agent_runs": agent_runs_data},
        )

    async def get_thread_messages(
        self, thread_id: str, order: str = "desc"
    ) -> MessagesResponse:
        """Get ALL messages for a thread.

        Args:
            thread_id: The thread ID
            order: Order by created_at: 'asc' or 'desc'

        Returns:
            MessagesResponse containing all messages
        """
        params = {"order": order}
        response = await self._request_with_retry(
            "GET", f"/threads/{thread_id}/messages", params=params
        )
        data = self._handle_response(response)

        messages = [from_dict(Message, msg_data) for msg_data in data["messages"]]
        return MessagesResponse(messages=messages)

    async def add_message_to_thread(self, thread_id: str, message: str) -> Message:
        """Add a simple message to a thread.

        Args:
            thread_id: The thread ID
            message: The message content

        Returns:
            The created message
        """
        # This endpoint expects form data, not JSON
        # Remove Content-Type for form data endpoint
        headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
        response = await self._request_with_retry(
            "POST",
            f"/threads/{thread_id}/messages/add",
            params={"message": message},
            headers=headers,
        )
        data = self._handle_response(response)
        return from_dict(Message, data)

    async def delete_message_from_thread(self, thread_id: str, message_id: str) -> None:
        """Delete a message from a thread.

        Args:
            thread_id: The thread ID
            message_id: The message ID

        Returns:
            None
        """
        response = await self._request_with_retry(
            "DELETE", f"/threads/{thread_id}/messages/{message_id}"
        )
        self._handle_response(response)

    async def create_message(
        self, thread_id: str, request: MessageCreateRequest
    ) -> Message:
        """Create a structured message in a thread.

        Args:
            thread_id: The thread ID
            request: The message creation request

        Returns:
            The created message
        """
        response = await self._request_with_retry(
            "POST", f"/threads/{thread_id}/messages", json=to_dict(request, exclude_none=False)
        )
        data = self._handle_response(response)
        return from_dict(Message, data)

    async def create_thread(self, name: Optional[str] = None) -> CreateThreadResponse:
        """Create a new thread with optional name.

        Args:
            name: Optional name for the thread/project

        Returns:
            CreateThreadResponse containing the new thread ID and project ID
        """
        # Remove Content-Type for form data endpoint
        headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
        form_data = None if name is None else {"name": name}
        response = await self._request_with_retry(
            "POST",
            "/threads",
            data=form_data,
            headers=headers,
        )
        data = self._handle_response(response)
        return from_dict(CreateThreadResponse, data)

    async def delete_thread(self, thread_id: str) -> None:
        """Delete a thread.
        
        Note: This endpoint is not currently implemented in the backend API.
        This method is kept for API compatibility but will raise NotImplementedError.
        
        Args:
            thread_id: The thread ID to delete
            
        Raises:
            NotImplementedError: Thread deletion is not supported by the backend API
        """
        raise NotImplementedError("Thread deletion is not implemented in the backend API")

    async def get_thread_agent(self, thread_id: str) -> ThreadAgentResponse:
        """Get the agent details for a specific thread.

        Args:
            thread_id: The thread ID

        Returns:
            ThreadAgentResponse with agent details and source information
        """
        response = await self._request_with_retry("GET", f"/thread/{thread_id}/agent")
        data = self._handle_response(response)

        agent_data = None
        if data.get("agent"):
            agent_data = from_dict(AgentResponse, data["agent"])

        return ThreadAgentResponse(
            agent=agent_data, source=data["source"], message=data["message"]
        )

    async def start_agent(
        self, thread_id: str, request: AgentStartRequest
    ) -> AgentStartResponse:
        """Start an agent for a specific thread.

        Args:
            thread_id: The thread ID
            request: The agent start request

        Returns:
            AgentStartResponse with agent run ID and status
        """
        response = await self._request_with_retry(
            "POST", f"/thread/{thread_id}/agent/start", json=to_dict(request, exclude_none=False)
        )
        data = self._handle_response(response)
        return from_dict(AgentStartResponse, data)

    async def stop_agent(self, agent_run_id: str) -> Dict[str, str]:
        """Stop a running agent.

        Args:
            agent_run_id: The agent run ID

        Returns:
            Status response
        """
        response = await self._request_with_retry("POST", f"/agent-run/{agent_run_id}/stop")
        data = self._handle_response(response)
        return data

    def get_agent_run_stream_url(
        self, agent_run_id: str, token: Optional[str] = None
    ) -> str:
        """Get the URL for streaming agent run responses.

        Args:
            agent_run_id: The agent run ID
            token: Optional authentication token for streaming

        Returns:
            The streaming URL
        """

        url = f"{self.base_url}/agent-run/{agent_run_id}/stream"
        return url


def create_threads_client(
    base_url: str,
    auth_token: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    timeout: float = 120.0,
) -> ThreadsClient:
    """Create a new ThreadsClient instance.

    Args:
        base_url: The base URL for the API
        auth_token: Optional authentication token
        custom_headers: Optional custom headers to include in requests
        timeout: Request timeout in seconds

    Returns:
        A new ThreadsClient instance
    """
    return ThreadsClient(
        base_url=base_url,
        auth_token=auth_token,
        custom_headers=custom_headers,
        timeout=timeout,
    )
