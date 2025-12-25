import types
import json
import pytest


class _FakeRequest:
    def __init__(self, method: str, url: str):
        self.method = method
        self.url = url


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict, request: _FakeRequest | None = None):
        self.status_code = status_code
        self._payload = payload
        self.request = request or _FakeRequest("GET", "/")

    def json(self):
        return self._payload

    @property
    def text(self) -> str:
        return json.dumps(self._payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeAsyncClient:
    """
    Minimal stub for httpx.AsyncClient used by the SDK clients.
    """

    def __init__(self, headers=None, timeout=None, base_url=None, limits=None, **kwargs):
        self.headers = headers or {}
        self.timeout = timeout
        self.base_url = base_url or ""
        self._limits = limits
        self.calls = []

    async def aclose(self):
        return None

    async def get(self, url, params=None, headers=None):
        self.calls.append(("GET", url, {"params": params, "headers": headers}))
        req = _FakeRequest("GET", url)

        # Used by Agent.details()
        if url.startswith("/agents/"):
            agent_id = url.split("/agents/")[1].split("/")[0]
            return _FakeResponse(
                200,
                {
                    "agent_id": agent_id,
                    "account_id": "acct",
                    "name": "A",
                    "system_prompt": "S",
                    "configured_mcps": [],
                    "custom_mcps": [],
                    "agentpress_tools": {},
                    "is_default": False,
                    "created_at": "now",
                },
                req,
            )

        # Used by Thread.get_messages() in some flows
        if url.endswith("/messages"):
            return _FakeResponse(200, {"messages": []}, req)

        return _FakeResponse(200, {}, req)

    async def post(self, url, json=None, params=None, data=None, headers=None):
        self.calls.append(("POST", url, {"json": json, "params": params, "data": data, "headers": headers}))
        req = _FakeRequest("POST", url)

        if url == "/agents":
            # Return minimal agent payload expected by AgentResponse
            return _FakeResponse(
                200,
                {
                    "agent_id": "agent_1",
                    "account_id": "acct",
                    "name": (json or {}).get("name", "A"),
                    "system_prompt": (json or {}).get("system_prompt", "S"),
                    "configured_mcps": (json or {}).get("configured_mcps", []) or [],
                    "custom_mcps": (json or {}).get("custom_mcps", []) or [],
                    "agentpress_tools": (json or {}).get("agentpress_tools", {}) or {},
                    "is_default": False,
                    "created_at": "now",
                },
                req,
            )

        if url == "/threads":
            return _FakeResponse(201, {"thread_id": "thread_1", "project_id": "proj_1"}, req)

        if url.endswith("/messages/add"):
            # Return minimal message payload expected by Message dataclass
            return _FakeResponse(
                201,
                {
                    "message_id": "msg_1",
                    "thread_id": "thread_1",
                    "type": "user",
                    "is_llm_message": True,
                    "content": "hi",
                    "created_at": "now",
                    "updated_at": "now",
                    "agent_id": "agent_1",
                    "agent_version_id": "ver_1",
                    "metadata": {},
                },
                req,
            )

        if url.endswith("/agent/start"):
            return _FakeResponse(200, {"agent_run_id": "run_1", "status": "started"}, req)

        return _FakeResponse(200, {}, req)

    async def put(self, url, json=None, params=None, headers=None):
        self.calls.append(("PUT", url, {"json": json, "params": params, "headers": headers}))
        req = _FakeRequest("PUT", url)
        return _FakeResponse(200, {}, req)

    async def delete(self, url, params=None, headers=None):
        self.calls.append(("DELETE", url, {"params": params, "headers": headers}))
        req = _FakeRequest("DELETE", url)
        return _FakeResponse(200, {}, req)

    async def request(self, method, url, **kwargs):
        method = method.upper()
        if method == "GET":
            return await self.get(url, params=kwargs.get("params"), headers=kwargs.get("headers"))
        if method == "POST":
            return await self.post(
                url,
                json=kwargs.get("json"),
                params=kwargs.get("params"),
                data=kwargs.get("data"),
                headers=kwargs.get("headers"),
            )
        if method == "PUT":
            return await self.put(url, json=kwargs.get("json"), params=kwargs.get("params"), headers=kwargs.get("headers"))
        if method == "DELETE":
            return await self.delete(url, params=kwargs.get("params"), headers=kwargs.get("headers"))
        return _FakeResponse(200, {}, _FakeRequest(method, url))


@pytest.mark.asyncio
async def test_agent_create_filters_tools(monkeypatch):
    import httpx
    from neurocluster import NeuroCluster, MCPTools, AgentPressTools

    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)

    # MCPTools will not make network calls until initialize(); we just set enabled_tools directly.
    mcp = MCPTools("http://localhost:4000/mcp/", "TestMCP")
    mcp.enabled_tools = ["tool_a", "tool_b"]

    async with NeuroCluster(api_key="k", api_url="http://localhost:8000/api") as client:
        agent = await client.Agent.create(
            name="My Agent",
            system_prompt="Hi",
            mcp_tools=[AgentPressTools.SB_FILES_TOOL, mcp],
            allowed_tools=["sb_files_tool", "tool_b"],
        )

        # Ensure the create call filtered MCP tools
        calls = client._agents_client.client.calls
        create_calls = [c for c in calls if c[0] == "POST" and c[1] == "/agents"]
        assert len(create_calls) == 1
        payload = create_calls[0][2]["json"]

        # AgentPress tool enabled flag should be true (key uses str Enum value)
        assert payload["agentpress_tools"]["sb_files_tool"]["enabled"] is True

        # MCP enabled tools should be filtered to allowed_tools intersection
        assert payload["custom_mcps"][0]["enabled_tools"] == ["tool_b"]

        # Returned Agent wrapper has id
        assert agent._agent_id == "agent_1"


@pytest.mark.asyncio
async def test_agent_run_starts_agent(monkeypatch):
    import httpx
    from neurocluster import NeuroCluster

    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)

    async with NeuroCluster(api_key="k", api_url="http://localhost:8000/api") as client:
        agent = await client.Agent.create(name="A", system_prompt="S", mcp_tools=[])
        thread = await client.Thread.create()

        run = await agent.run("hello", thread)
        assert run._agent_run_id == "run_1"

