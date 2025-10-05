from .api import agents, threads
from .agent import NeuroClusterAgent
from .thread import NeuroClusterThread
from .tools import AgentPressTools, MCPTools


class NeuroCluster:
    def __init__(self, api_key: str, api_url="https://supernova.app/api"):
        self._agents_client = agents.create_agents_client(api_url, api_key)
        self._threads_client = threads.create_threads_client(api_url, api_key)

        self.Agent = NeuroClusterAgent(self._agents_client)
        self.Thread = NeuroClusterThread(self._threads_client)
