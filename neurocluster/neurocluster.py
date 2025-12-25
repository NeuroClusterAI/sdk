import logging
from typing import Optional, Any
from .api import agents, threads, versions
from .agent import NeuroClusterAgent
from .thread import NeuroClusterThread
from .tools import AgentPressTools, MCPTools

logger = logging.getLogger("neurocluster")


class NeuroCluster:
    """
    Main NeuroCluster SDK client.
    
    Integration clients (Pipedream, Composio) are lazy-loaded - they're only
    initialized when accessed, keeping the SDK modular.
    """
    
    def __init__(self, api_key: str, api_url="https://api.neurocluster.com/api"):
        self._api_key = api_key
        self._api_url = api_url
        
        logger.debug(f"Initializing NeuroCluster client with API URL: {api_url}")
        
        # Core clients (always initialized)
        self._agents_client = agents.create_agents_client(api_url, api_key)
        self._threads_client = threads.create_threads_client(api_url, api_key)
        self._versions_client = versions.create_versions_client(api_url, api_key)
        
        # Integration clients (lazy-loaded)
        self._pipedream_client: Optional[Any] = None
        self._composio_client: Optional[Any] = None

        # Core API access
        self.Agent = NeuroClusterAgent(self._agents_client)
        self.Thread = NeuroClusterThread(self._threads_client)
        self.Versions = self._versions_client
        
        logger.info("NeuroCluster client initialized successfully")

    @property
    def Pipedream(self):
        """Lazy-loaded Pipedream client. Only initialized when accessed."""
        if self._pipedream_client is None:
            logger.debug("Initializing Pipedream client (lazy load)")
            from .api import pipedream
            self._pipedream_client = pipedream.create_pipedream_client(
                self._api_url, self._api_key
            )
        return self._pipedream_client

    @property
    def Composio(self):
        """Lazy-loaded Composio client. Only initialized when accessed."""
        if self._composio_client is None:
            logger.debug("Initializing Composio client (lazy load)")
            from .api import composio
            self._composio_client = composio.create_composio_client(
                self._api_url, self._api_key
            )
        return self._composio_client

    async def close(self) -> None:
        """Close underlying HTTP clients."""
        logger.debug("Closing NeuroCluster client connections")
        
        # Be tolerant of partial initialization / double-close.
        clients = [
            self._agents_client,
            self._threads_client,
            self._versions_client,
        ]
        
        # Only close integration clients if they were initialized
        if self._pipedream_client is not None:
            clients.append(self._pipedream_client)
        if self._composio_client is not None:
            clients.append(self._composio_client)
        
        for c in clients:
            close = getattr(c, "close", None)
            if close:
                await close()
        
        logger.debug("All client connections closed")

    async def __aenter__(self) -> "NeuroCluster":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
