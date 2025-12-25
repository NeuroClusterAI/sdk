import json
import re
import xml.dom.minidom
from typing import AsyncGenerator, Optional, Any

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


# --- ANSI Colors ---
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def try_parse_json(json_str: str) -> Optional[Any]:
    """Utility function to safely parse JSON strings."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def format_xml_if_valid(content: str) -> str:
    """
    Check if content is XML and format it prettily if so.
    Returns the original content if it's not valid XML.
    """
    if not content or not content.strip():
        return content

    # Quick check if it looks like XML
    stripped_content = content.strip()
    if not (stripped_content.startswith("<") and stripped_content.endswith(">")):
        return content

    try:
        # Parse and pretty-print the XML
        dom = xml.dom.minidom.parseString(stripped_content)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Remove empty lines and the XML declaration for cleaner output
        lines = [line for line in pretty_xml.split("\n") if line.strip()]
        if lines and lines[0].startswith("<?xml"):
            lines = lines[1:]  # Remove XML declaration

        # Apply syntax highlighting
        highlighted_lines = []
        for line in lines:
            highlighted_line = _highlight_xml_line(line)
            highlighted_lines.append(highlighted_line)

        return "\n" + "\n".join(highlighted_lines)
    except Exception:
        # If XML parsing fails, return original content
        return content


def _highlight_xml_line(line: str) -> str:
    """
    Apply simple syntax highlighting to an XML line.
    """
    if not line.strip():
        return line

    # Process the line character by character to avoid regex conflicts
    result = []
    i = 0
    while i < len(line):
        char = line[i]

        if char == "<":
            # Find the end of the tag
            tag_end = line.find(">", i)
            if tag_end == -1:
                result.append(char)
                i += 1
                continue

            # Extract the full tag
            tag_content = line[i : tag_end + 1]
            highlighted_tag = _highlight_xml_tag(tag_content)
            result.append(highlighted_tag)
            i = tag_end + 1
        else:
            result.append(char)
            i += 1

    return "".join(result)


def _highlight_xml_tag(tag: str) -> str:
    """
    Highlight a complete XML tag (from < to >).
    """
    if not tag.startswith("<") or not tag.endswith(">"):
        return tag

    # Check if it's a closing tag
    is_closing = tag.startswith("</")

    # Extract tag name and attributes
    if is_closing:
        # For closing tags like </function_calls>
        tag_name = tag[2:-1].strip()
        return f"{Colors.YELLOW}</{Colors.BLUE}{Colors.BOLD}{tag_name}{Colors.ENDC}{Colors.YELLOW}>{Colors.ENDC}"
    else:
        # For opening tags with possible attributes
        inner = tag[1:-1]  # Remove < and >

        # Split on first space to separate tag name from attributes
        parts = inner.split(" ", 1)
        tag_name = parts[0]

        result = f"{Colors.YELLOW}<{Colors.BLUE}{Colors.BOLD}{tag_name}{Colors.ENDC}"

        if len(parts) > 1:
            # Process attributes
            attrs = parts[1]
            highlighted_attrs = _highlight_attributes(attrs)
            result += " " + highlighted_attrs

        result += f"{Colors.YELLOW}>{Colors.ENDC}"
        return result


def _highlight_attributes(attrs: str) -> str:
    """
    Highlight XML attributes.
    """
    # Use regex to find attribute="value" patterns
    pattern = r'([a-zA-Z_][a-zA-Z0-9_-]*)(=)(["\'])([^"\']*)\3'

    def replace_attr(match):
        attr_name = match.group(1)
        equals = match.group(2)
        quote = match.group(3)
        value = match.group(4)
        return f"{Colors.CYAN}{attr_name}{Colors.ENDC}{equals}{quote}{Colors.GREEN}{value}{Colors.ENDC}{quote}"

    return re.sub(pattern, replace_attr, attrs)


async def print_stream(stream: AsyncGenerator[str, None]):
    """
    Simple stream printer that processes async string generator.
    Uses StreamParser for typed event handling.
    Follows the same output format as stream_test.py.
    """
    parser = StreamParser()
    
    async for event in parser.parse(stream):
        if isinstance(event, StreamStartEvent):
            print(f"{Colors.BLUE}{Colors.BOLD}🚀 [STREAM START]{Colors.ENDC}")
        
        elif isinstance(event, StatusEvent):
            print(
                f"{Colors.CYAN}ℹ️  [STATUS] {Colors.BOLD}{event.status_type}{Colors.ENDC}"
                f"{Colors.CYAN} {event.finish_reason or 'received'}{Colors.ENDC}"
            )
        
        elif isinstance(event, ToolUseDetectedEvent):
            print(f"\n{Colors.YELLOW}🔧 [TOOL USE DETECTED]{Colors.ENDC}")
        
        elif isinstance(event, ToolInvocationEvent):
            print(
                f'{Colors.BLUE}⚡ [TOOL UPDATE] Calling function: '
                f'{Colors.BOLD}"{event.function_name}"{Colors.ENDC}'
            )
        
        elif isinstance(event, ToolUseWaitingEvent):
            print(f"{Colors.YELLOW}⏳ [TOOL USE WAITING]{Colors.ENDC}")
        
        elif isinstance(event, AssistantMessageEvent):
            # Format XML content prettily if it's XML
            formatted_content = format_xml_if_valid(event.content)
            print()  # New line
            print(f"{Colors.GREEN}💬 [MESSAGE] {Colors.ENDC}{formatted_content}")
        
        elif isinstance(event, ToolResultEvent):
            if event.success:
                output = json.dumps(event.output) if event.output else "{}"
                # Check if output is long enough to truncate or format as XML
                if len(output) > 80:
                    formatted_output = format_xml_if_valid(output)
                    if formatted_output != output:
                        output_preview = formatted_output
                    else:
                        output_preview = output[:80] + "..."
                else:
                    output_preview = format_xml_if_valid(output)
                    if output_preview == "{}":
                        output_preview = "No answer found."
                
                print(
                    f'{Colors.GREEN}✅ [TOOL RESULT] {Colors.BOLD}"{event.tool_name}"{Colors.ENDC}'
                    f'{Colors.GREEN} | Success! Output: {Colors.ENDC}{output_preview}'
                )
            else:
                error = json.dumps(event.error) if event.error else "{}"
                formatted_error = format_xml_if_valid(error)
                print(
                    f'{Colors.RED}❌ [TOOL RESULT] {Colors.BOLD}"{event.tool_name}"{Colors.ENDC}'
                    f'{Colors.RED} | Failure! Error: {Colors.ENDC}{formatted_error}'
                )
        
        elif isinstance(event, ParseErrorEvent):
            print(f"{Colors.RED}❌ [PARSE ERROR] {event.error_message}{Colors.ENDC}")
        
        elif isinstance(event, StreamEndEvent):
            pass  # Stream end, no output needed
