from .api.threads import AgentStartRequest
from .thread import Thread, AgentRun
from .tools import NeuroClusterTools
from .api.agents import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentsClient,
    CustomMCP,
)
from .tool_utils import process_mcp_tools, filter_existing_tools


class Agent:
    def __init__(
        self,
        client: AgentsClient,
        agent_id: str,
        model: str = "anthropic/claude-sonnet-4-20250514",
    ):
        self._client = client
        self._agent_id = agent_id
        self._model = model

    async def update(
        self,
        name: str | None = None,
        system_prompt: str | None = None,
        mcp_tools: list[NeuroClusterTools] | None = None,
        allowed_tools: list[str] | None = None,
        configured_mcps: list[CustomMCP] | None = None,
        replace_mcps: bool | None = None,
    ):
        if mcp_tools:
            # Process new tools from scratch
            agentpress_tools, custom_mcps = process_mcp_tools(mcp_tools, allowed_tools)
        else:
            # Update existing tools - fetch current config and filter
            agent_details = await self.details()
            agentpress_tools = agent_details.agentpress_tools
            configured_mcps = agent_details.configured_mcps if configured_mcps is None else configured_mcps
            custom_mcps = agent_details.custom_mcps
            if allowed_tools:
                filter_existing_tools(agentpress_tools, custom_mcps, allowed_tools)

        await self._client.update_agent(
            self._agent_id,
            AgentUpdateRequest(
                name=name,
                system_prompt=system_prompt,
                configured_mcps=configured_mcps,
                custom_mcps=custom_mcps,
                agentpress_tools=agentpress_tools,
                replace_mcps=replace_mcps,
            ),
        )

    async def details(self):
        response = await self._client.get_agent(self._agent_id)
        return response

    async def run(
        self,
        prompt: str,
        thread: Thread,
        model: str | None = None,
        enable_prompt_caching: bool | None = None,
    ):
        await thread.add_message(prompt)
        response = await thread._client.start_agent(
            thread._thread_id,
            AgentStartRequest(
                agent_id=self._agent_id,
                model_name=model or self._model,
                enable_prompt_caching=enable_prompt_caching,
            ),
        )
        return AgentRun(thread, response.agent_run_id)


class NeuroClusterAgent:
    def __init__(self, client: AgentsClient):
        self._client = client

    async def create(
        self,
        name: str,
        system_prompt: str,
        mcp_tools: list[NeuroClusterTools] | None = None,
        allowed_tools: list[str] | None = None,
        configured_mcps: list[CustomMCP] | None = None,
    ) -> Agent:
        if mcp_tools is None:
            mcp_tools = []
        
        agentpress_tools, custom_mcps = process_mcp_tools(mcp_tools, allowed_tools)

        agent = await self._client.create_agent(
            AgentCreateRequest(
                name=name,
                system_prompt=system_prompt,
                configured_mcps=configured_mcps,
                custom_mcps=custom_mcps,
                agentpress_tools=agentpress_tools,
            )
        )

        return Agent(self._client, agent.agent_id)

    async def get(self, agent_id: str) -> Agent:
        agent = await self._client.get_agent(agent_id)
        return Agent(self._client, agent.agent_id)
