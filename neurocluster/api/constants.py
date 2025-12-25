"""Constants for API clients."""


class APIHeaders:
    """HTTP header names used by the API."""
    API_KEY = "X-API-Key"
    CONTENT_TYPE = "Content-Type"
    ACCEPT = "Accept"
    MCP_URL = "X-MCP-URL"
    MCP_TYPE = "X-MCP-Type"
    MCP_HEADERS = "X-MCP-Headers"


class ContentTypes:
    """HTTP content types."""
    JSON = "application/json"


class MessageTypes:
    """Message type values."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    STATUS = "status"
    ASSISTANT_RESPONSE_END = "assistant_response_end"

