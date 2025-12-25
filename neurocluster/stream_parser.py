"""Stream parser for processing agent run stream responses."""

import json
import re
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, Any, List, Dict


@dataclass
class StreamEvent:
    """Base class for stream events."""
    event_type: str


@dataclass
class StatusEvent(StreamEvent):
    """Status event from the stream."""
    status_type: str
    message: Optional[str] = None
    finish_reason: Optional[str] = None
    
    def __init__(
        self, 
        status_type: str, 
        message: Optional[str] = None, 
        finish_reason: Optional[str] = None
    ):
        super().__init__(event_type="status")
        self.status_type = status_type
        self.message = message
        self.finish_reason = finish_reason


@dataclass
class AssistantChunkEvent(StreamEvent):
    """Assistant streaming chunk event (partial message)."""
    sequence: int
    content: str
    full_text: str  # Accumulated full text so far
    
    def __init__(self, sequence: int, content: str, full_text: str):
        super().__init__(event_type="assistant_chunk")
        self.sequence = sequence
        self.content = content
        self.full_text = full_text


@dataclass
class AssistantMessageEvent(StreamEvent):
    """Complete assistant message event."""
    message_id: str
    role: str
    content: str
    
    def __init__(self, message_id: str, role: str, content: str):
        super().__init__(event_type="assistant_message")
        self.message_id = message_id
        self.role = role
        self.content = content


@dataclass
class ToolUseDetectedEvent(StreamEvent):
    """Event indicating tool use was detected in the stream."""
    
    def __init__(self):
        super().__init__(event_type="tool_use_detected")


@dataclass
class ToolInvocationEvent(StreamEvent):
    """Event when a specific tool is being invoked."""
    function_name: str
    
    def __init__(self, function_name: str):
        super().__init__(event_type="tool_invocation")
        self.function_name = function_name


@dataclass
class ToolUseWaitingEvent(StreamEvent):
    """Event when tool use is complete and waiting for results."""
    
    def __init__(self):
        super().__init__(event_type="tool_use_waiting")


@dataclass
class ToolResultEvent(StreamEvent):
    """Tool execution result event."""
    tool_name: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    
    def __init__(
        self, 
        tool_name: str, 
        success: bool, 
        output: Optional[Any] = None, 
        error: Optional[str] = None
    ):
        super().__init__(event_type="tool_result")
        self.tool_name = tool_name
        self.success = success
        self.output = output
        self.error = error


@dataclass
class StreamStartEvent(StreamEvent):
    """Event indicating the stream has started."""
    
    def __init__(self):
        super().__init__(event_type="stream_start")


@dataclass
class StreamEndEvent(StreamEvent):
    """Event indicating the stream has ended."""
    
    def __init__(self):
        super().__init__(event_type="stream_end")


@dataclass
class ParseErrorEvent(StreamEvent):
    """Event for parse errors during stream processing."""
    error_message: str
    raw_data: Optional[str] = None
    
    def __init__(self, error_message: str, raw_data: Optional[str] = None):
        super().__init__(event_type="parse_error")
        self.error_message = error_message
        self.raw_data = raw_data


class StreamParser:
    """
    Parses agent run stream responses into typed events.
    
    This class processes async string generators (from SSE streams) and
    yields typed StreamEvent objects that can be handled by consumers.
    
    Usage:
        parser = StreamParser()
        async for event in parser.parse(stream):
            if isinstance(event, StatusEvent):
                print(f"Status: {event.status_type}")
            elif isinstance(event, AssistantMessageEvent):
                print(f"Message: {event.content}")
            # ... handle other event types
    """
    
    def __init__(self):
        self._chunks: List[Dict[str, Any]] = []
        self._parsing_state = "text"  # "text", "in_function_call", "function_call_ended"
        self._current_function_name: Optional[str] = None
        self._stream_started = False
        self._invoke_name_regex = re.compile(r'<invoke\s+name="([^"]+)"')
    
    def reset(self):
        """Reset parser state for a new stream."""
        self._chunks = []
        self._parsing_state = "text"
        self._current_function_name = None
        self._stream_started = False
    
    def _try_parse_json(self, json_str: str) -> Optional[Any]:
        """Safely parse JSON strings."""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def _rebuild_full_text(self) -> str:
        """Rebuild full text from sorted chunks."""
        sorted_chunks = sorted(self._chunks, key=lambda c: c.get("sequence", 0))
        
        full_text_parts = []
        for chunk in sorted_chunks:
            content = chunk.get("content", "")
            if content:
                parsed_content = self._try_parse_json(content)
                if parsed_content and "content" in parsed_content:
                    full_text_parts.append(parsed_content["content"])
        
        return "".join(full_text_parts)
    
    def _handle_status(self, data: Dict[str, Any]) -> StatusEvent:
        """Process a status event."""
        status_details = self._try_parse_json(data.get("content", "{}")) or {}
        if data.get("status"):
            status_details["status_type"] = data["status"]
        if data.get("message"):
            status_details["message"] = data["message"]
        
        full_status = {**data, **status_details}
        return StatusEvent(
            status_type=full_status.get("status_type", full_status.get("status", "unknown")),
            message=full_status.get("message"),
            finish_reason=full_status.get("finish_reason", "received"),
        )
    
    def _handle_assistant_chunk(self, data: Dict[str, Any]) -> List[StreamEvent]:
        """Process an assistant chunk event. May return multiple events."""
        events: List[StreamEvent] = []
        
        sequence = data.get("sequence")
        content = data.get("content", "")
        
        # Add chunk to collection
        self._chunks.append(data)
        
        # Rebuild full text from all chunks
        full_text = self._rebuild_full_text()
        
        # Emit the chunk event
        events.append(AssistantChunkEvent(
            sequence=sequence,
            content=content,
            full_text=full_text,
        ))
        
        # Check for function call state transitions
        if self._parsing_state == "text":
            if "<function_calls>" in full_text:
                self._parsing_state = "in_function_call"
                events.append(ToolUseDetectedEvent())
        
        elif self._parsing_state == "in_function_call":
            if self._current_function_name is None:
                match = self._invoke_name_regex.search(full_text)
                if match:
                    self._current_function_name = match.group(1)
                    events.append(ToolInvocationEvent(self._current_function_name))
            
            if "</function_calls>" in full_text:
                self._parsing_state = "function_call_ended"
                events.append(ToolUseWaitingEvent())
                self._current_function_name = None
        
        return events
    
    def _handle_assistant_message(self, data: Dict[str, Any]) -> List[StreamEvent]:
        """Process a complete assistant message. May return multiple events."""
        events: List[StreamEvent] = []
        
        message_id = data.get("message_id")
        content = data.get("content", "")
        
        if content:
            parsed_content = self._try_parse_json(content)
            if parsed_content:
                events.append(AssistantMessageEvent(
                    message_id=message_id,
                    role=parsed_content.get("role", "unknown"),
                    content=parsed_content.get("content", ""),
                ))
            else:
                events.append(ParseErrorEvent(
                    error_message="Failed to parse assistant message content",
                    raw_data=content,
                ))
        
        # Reset state for next message
        self._chunks = []
        self._parsing_state = "text"
        self._current_function_name = None
        
        return events
    
    def _handle_tool_result(self, data: Dict[str, Any]) -> StreamEvent:
        """Process a tool result event."""
        content = data.get("content", "")
        
        if not content:
            return ParseErrorEvent("No content in tool result message")
        
        parsed_content = self._try_parse_json(content)
        if not parsed_content:
            return ParseErrorEvent("Failed to parse tool result content", content)
        
        tool_execution = parsed_content.get("tool_execution", {})
        tool_name = tool_execution.get("function_name", "unknown")
        result = tool_execution.get("result", {})
        
        return ToolResultEvent(
            tool_name=tool_name,
            success=result.get("success", False),
            output=result.get("output"),
            error=result.get("error"),
        )
    
    async def parse(self, stream: AsyncGenerator[str, None]) -> AsyncGenerator[StreamEvent, None]:
        """
        Parse a stream and yield typed events.
        
        Args:
            stream: Async generator yielding raw SSE lines
            
        Yields:
            StreamEvent subclass instances
        """
        self.reset()
        
        async for line in stream:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Parse stream data lines
            if line.startswith("data: "):
                json_str = line[6:]  # Remove "data: " prefix
                
                data = self._try_parse_json(json_str)
                if not data:
                    yield ParseErrorEvent("Failed to parse JSON", json_str)
                    continue
                
                event_type = data.get("type", "unknown")
                
                # Emit stream start on first event
                if not self._stream_started:
                    self._stream_started = True
                    yield StreamStartEvent()
                
                if event_type == "status":
                    yield self._handle_status(data)
                
                elif event_type == "assistant":
                    message_id = data.get("message_id")
                    sequence = data.get("sequence")
                    
                    if message_id is None and sequence is not None:
                        # Streaming chunk
                        for event in self._handle_assistant_chunk(data):
                            yield event
                    elif message_id is not None:
                        # Complete message
                        for event in self._handle_assistant_message(data):
                            yield event
                
                elif event_type == "tool":
                    yield self._handle_tool_result(data)
        
        # Stream ended
        yield StreamEndEvent()

