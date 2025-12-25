# NeuroCluster SDK

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

A Python SDK that enables you to create, manage, and interact with AI Workers on [NeuroCluster](https://neurocluster.com).

## 📦 Installation

Install directly from the GitHub repository:

```bash
pip install "neurocluster @ git+https://github.com/NeuroClusterAI/sdk.git@main"
```

Or using uv:

```bash
uv add "neurocluster @ git+https://github.com/NeuroClusterAI/sdk.git@main"
```

## 🔧 Quick Start

```python
import asyncio
from neurocluster import NeuroCluster, MCPTools

async def main():
    mcp_tools = MCPTools(
        "http://localhost:4000/mcp/",  # Point to any HTTP MCP server
        "NeuroCluster",
    )
    await mcp_tools.initialize()

    # Initialize the client (and make sure we close underlying HTTP connections)
    async with NeuroCluster(api_key="your-api-key") as client:

        # Create an agent
        agent = await client.Agent.create(
            name="My Assistant",
            system_prompt="You are a helpful AI assistant.",
            mcp_tools=[mcp_tools],
            allowed_tools=["get_wind_direction"],
        )

        # Create a conversation thread
        thread = await client.Thread.create()

        # Run the agent
        run = await agent.run("Hello, how are you?", thread)

        # Stream the response
        stream = await run.get_stream()
        async for chunk in stream:
            print(chunk, end="")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔑 Environment Setup

Get your API key from [https://app.neurocluster.com/settings/api-keys](https://app.neurocluster.com/settings/api-keys)

## ✨ Features

### Agent Management
- Create, update, and delete agents
- Configure MCP tools (both configured and custom)
- Manage AgentPress tools
- Generate agent icons automatically
- Export and import agent configurations

### Agent Versioning
- Create multiple versions of agents
- Compare versions
- Activate specific versions
- Rollback to previous versions
- Update version details

### Thread Management
- Create and manage conversation threads
- Add and delete messages
- Get thread history
- Start and stop agent runs
- Stream agent responses

### Advanced Features
- Icon generation for agents
- JSON export/import for agent configurations
- Analyze JSON before import to check requirements
- Full MCP tool integration support
- **Modular integration platforms** (lazy-loaded):
  - Pipedream integration (profiles, apps, tools, MCP connections)
  - Composio integration (toolkits, profiles, tools, triggers)

## 📚 API Reference

### Direct Client Usage

You can also use the API clients directly for more control:

```python
from neurocluster.api import agents

# Basic usage with auth token
client = agents.create_agents_client(
    base_url="https://api.neurocluster.com/api",
    auth_token="your-jwt-token"
)

# Usage with custom headers
client = agents.create_agents_client(
    base_url="https://api.neurocluster.com/api",
    auth_token="your-jwt-token",
    custom_headers={
        "X-Custom-Header": "custom-value",
        "X-API-Version": "v1"
    }
)

# Using the client with type safety
async with client:
    # Get all agents
    agents_response = await client.get_agents(page=1, limit=10, search="chatbot")
    print(f"Found {agents_response.pagination.total} agents")
    
    # Get specific agent
    agent = await client.get_agent("agent-id")
    print(f"Agent name: {agent.name}")
    
    # Create new agent
    from neurocluster.api.agents import AgentCreateRequest
    create_request = AgentCreateRequest(
        name="My Agent",
        system_prompt="You are a helpful assistant",
        description="A custom agent for my project"
    )
    new_agent = await client.create_agent(create_request)
    
    # Update agent
    from neurocluster.api.agents import AgentUpdateRequest
    update_request = AgentUpdateRequest(
        name="Updated Agent Name",
        system_prompt="Updated system prompt"
    )
    updated_agent = await client.update_agent("agent-id", update_request)
    
    # Get agent tools
    tools = await client.get_agent_tools("agent-id")
    print(f"AgentPress tools: {len(tools.agentpress_tools)}")
    print(f"MCP tools: {len(tools.mcp_tools)}")
    
    # Update Pipedream tools
    from neurocluster.api.agents import PipedreamToolsUpdateRequest
    pipedream_request = PipedreamToolsUpdateRequest(enabled_tools=["tool1", "tool2"])
    result = await client.update_pipedream_tools("agent-id", "profile-id", pipedream_request)
```

### Agent Operations

```python
# Create an agent
agent = await client.Agent.create(
    name="My Agent",
    system_prompt="You are helpful",
    mcp_tools=[mcp_tools],
    allowed_tools=["tool1", "tool2"]
)

# Get agent details
agent = await client.Agent.get(agent_id)

# Update agent
await agent.update(
    name="Updated Name",
    system_prompt="New prompt"
)

# Generate icon
from neurocluster.api.agents import AgentIconGenerationRequest
icon = await agent._client.generate_icon(
    AgentIconGenerationRequest(name="My Agent", description="A helpful agent")
)

# Export agent
export_data = await agent._client.export_agent(agent_id)

# Import agent
from neurocluster.api.agents import JsonImportRequestModel
result = await client._agents_client.import_json(
    JsonImportRequestModel(json_data=export_data)
)
```

### Version Management

```python
from neurocluster.neurocluster.api import versions

versions_client = versions.create_versions_client(
    base_url="https://api.neurocluster.com/api",
    auth_token="your-api-key"
)

# Get all versions
all_versions = await versions_client.get_versions(agent_id)

# Create a new version
from neurocluster.neurocluster.api.versions import CreateVersionRequest
new_version = await versions_client.create_version(
    agent_id,
    CreateVersionRequest(
        system_prompt="Updated prompt",
        version_name="v2.0"
    )
)

# Compare versions
comparison = await versions_client.compare_versions(
    agent_id, version1_id, version2_id
)

# Activate a version
await versions_client.activate_version(agent_id, version_id)
```

### Thread Operations

```python
# Create a thread
thread = await client.Thread.create(name="My Thread")

# Add a message
await thread.add_message("Hello!")

# Get messages
messages = await thread.get_messages()

# Run agent with custom options
run = await agent.run(
    "What's the weather?",
    thread,
    model="anthropic/claude-sonnet-4-20250514",
    enable_prompt_caching=True
)

# Stream response
stream = await run.get_stream()
async for chunk in stream:
    print(chunk, end="")
```

## 🧪 Running Examples

```bash
# Install dependencies
uv sync

# Run the main example
PYTHONPATH=$(pwd) uv run example/example.py
```

### Integration Platforms (Optional)

The SDK supports both **Pipedream** and **Composio** integration platforms. These are **lazy-loaded** - they're only initialized when you access them, keeping the SDK lightweight and modular.

#### Pipedream Integration

```python
# Pipedream client is only initialized when accessed
# Get available Pipedream apps
apps = await client.Pipedream.get_apps(q="slack", category="communication")

# Get tools for a specific app
tools = await client.Pipedream.get_app_tools("slack")

# List your Pipedream profiles
profiles = await client.Pipedream.get_profiles(app_slug="slack")

# Create a new profile
from neurocluster.api.pipedream import CreateProfileRequest
profile = await client.Pipedream.create_profile(
    CreateProfileRequest(
        profile_name="My Slack Profile",
        app_slug="slack",
        app_name="Slack",
        enabled_tools=["send_message", "list_channels"]
    )
)

# Discover MCP servers
mcp_servers = await client.Pipedream.discover_mcp_servers(app_slug="slack")

# Create MCP connection
connection = await client.Pipedream.create_mcp_connection(
    app_slug="slack",
    oauth_app_id="oauth_123"
)

# Update profile tools
from neurocluster.api.pipedream import UpdateProfileRequest
updated = await client.Pipedream.update_profile(
    profile.profile_id,
    UpdateProfileRequest(enabled_tools=["send_message", "list_channels", "get_user"])
)
```

#### Composio Integration

```python
# Composio client is only initialized when accessed
# Get available Composio toolkits
toolkits = await client.Composio.get_toolkits(search="slack", category="communication")

# Get toolkit details
toolkit = await client.Composio.get_toolkit_details("slack")

# Get tools for a toolkit
tools = await client.Composio.get_tools("slack", limit=50)

# Create a profile
profile = await client.Composio.create_profile(
    toolkit_slug="slack",
    profile_name="My Slack Profile",
    display_name="Slack Integration"
)

# List your Composio profiles
profiles = await client.Composio.get_profiles(toolkit_slug="slack")

# Discover tools for a profile
tools = await client.Composio.discover_tools(profile.profile_id)

# Get MCP configuration
mcp_config = await client.Composio.get_profile_mcp_config(profile.profile_id)
```

#### Choosing Between Pipedream and Composio

- **Pipedream**: Better for workflow automation, 2,700+ integrations, code-first approach
- **Composio**: Better for AI agents, strong trigger support, toolkit-based organization

You can use both in the same project - they're independent and only initialized when accessed.

## 🔄 Migration Guide

### From Previous Versions

All functionality remains backward compatible. New features include:
- Agent versioning support
- Icon generation
- Export/import functionality
- Enhanced MCP configuration support (configured_mcps)
- Prompt caching support in agent runs
- Full Pipedream integration (profiles, apps, tools, MCP connections)
- Full Composio integration (toolkits, profiles, tools, triggers)
- Automatic retry logic for transient failures
- Improved error handling and type safety

## 🐛 Troubleshooting

Having issues? Check out the [Troubleshooting Guide](TROUBLESHOOTING.md) for:
- Common error solutions
- Network and connection issues
- Integration platform problems
- Performance optimization tips
- Debugging techniques
