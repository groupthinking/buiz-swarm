"""
Model Context Protocol (MCP) Client Implementation.

MCP is an open protocol that standardizes how applications provide context to LLMs.
This client enables agents to discover and use tools/resources from MCP servers.

Reference: https://modelcontextprotocol.io/
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from enum import Enum
from datetime import datetime

import httpx
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MCPError(Exception):
    """Error from MCP server or client."""
    pass


class MCPServerStatus(str, Enum):
    """Status of an MCP server connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPTool:
    """Tool available from an MCP server."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_id: str
    handler: Optional[Callable[[Dict[str, Any]], Any]] = None
    
    def to_claude_format(self) -> Dict[str, Any]:
        """Convert to Claude tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


@dataclass
class MCPResource:
    """Resource available from an MCP server."""
    uri: str
    name: str
    description: str
    mime_type: str
    server_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


@dataclass
class MCPServer:
    """MCP server configuration and state."""
    server_id: str
    name: str
    url: str
    status: MCPServerStatus = MCPServerStatus.DISCONNECTED
    tools: List[MCPTool] = field(default_factory=list)
    resources: List[MCPResource] = field(default_factory=list)
    last_connected: Optional[datetime] = None
    error_message: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0


class MCPToolCall(BaseModel):
    """Tool call request."""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MCPToolResult(BaseModel):
    """Tool call result."""
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class MCPClient:
    """
    Client for Model Context Protocol servers.
    
    Manages connections to multiple MCP servers, discovers tools and resources,
    and routes tool calls to appropriate servers.
    """
    
    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
        self._tool_index: Dict[str, MCPTool] = {}
        self._resource_index: Dict[str, MCPResource] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=settings.MCP_TIMEOUT_SECONDS,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return self._http_client
    
    async def register_server(
        self,
        server_id: str,
        name: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        auto_connect: bool = True
    ) -> MCPServer:
        """
        Register an MCP server.
        
        Args:
            server_id: Unique identifier for the server
            name: Human-readable name
            url: Base URL of the MCP server
            headers: Optional headers for authentication
            auto_connect: Whether to connect immediately
            
        Returns:
            MCPServer instance
        """
        server = MCPServer(
            server_id=server_id,
            name=name,
            url=url.rstrip('/'),
            headers=headers or {}
        )
        
        self._servers[server_id] = server
        
        if auto_connect:
            await self.connect_server(server_id)
        
        logger.info(f"Registered MCP server: {name} ({server_id})")
        return server
    
    async def connect_server(self, server_id: str) -> bool:
        """
        Connect to an MCP server and discover capabilities.
        
        Args:
            server_id: Server to connect to
            
        Returns:
            True if connection successful
        """
        if server_id not in self._servers:
            raise MCPError(f"Server {server_id} not registered")
        
        server = self._servers[server_id]
        server.status = MCPServerStatus.CONNECTING
        
        try:
            client = await self._get_http_client()
            
            # Initialize connection
            init_response = await client.post(
                f"{server.url}/mcp/initialize",
                headers=server.headers,
                json={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "clientInfo": {
                        "name": "BuizSwarm",
                        "version": "1.0.0"
                    }
                }
            )
            
            if init_response.status_code != 200:
                raise MCPError(f"Initialization failed: {init_response.text}")
            
            init_data = init_response.json()
            server_capabilities = init_data.get("capabilities", {})
            
            # Discover tools if supported
            if "tools" in server_capabilities:
                await self._discover_tools(server)
            
            # Discover resources if supported
            if "resources" in server_capabilities:
                await self._discover_resources(server)
            
            server.status = MCPServerStatus.CONNECTED
            server.last_connected = datetime.utcnow()
            server.error_message = None
            
            logger.info(f"Connected to MCP server: {server.name}")
            return True
            
        except Exception as e:
            server.status = MCPServerStatus.ERROR
            server.error_message = str(e)
            logger.error(f"Failed to connect to MCP server {server.name}: {e}")
            return False
    
    async def _discover_tools(self, server: MCPServer) -> None:
        """Discover tools from an MCP server."""
        try:
            client = await self._get_http_client()
            response = await client.post(
                f"{server.url}/mcp/tools/list",
                headers=server.headers,
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                tools_data = data.get("tools", [])
                
                server.tools = []
                for tool_data in tools_data:
                    tool = MCPTool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {}),
                        server_id=server.server_id
                    )
                    server.tools.append(tool)
                    
                    # Add to global tool index
                    tool_key = f"{server.server_id}:{tool.name}"
                    self._tool_index[tool_key] = tool
                
                logger.info(f"Discovered {len(server.tools)} tools from {server.name}")
        except Exception as e:
            logger.error(f"Failed to discover tools from {server.name}: {e}")
    
    async def _discover_resources(self, server: MCPServer) -> None:
        """Discover resources from an MCP server."""
        try:
            client = await self._get_http_client()
            response = await client.post(
                f"{server.url}/mcp/resources/list",
                headers=server.headers,
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                resources_data = data.get("resources", [])
                
                server.resources = []
                for resource_data in resources_data:
                    resource = MCPResource(
                        uri=resource_data["uri"],
                        name=resource_data.get("name", ""),
                        description=resource_data.get("description", ""),
                        mime_type=resource_data.get("mimeType", "application/json"),
                        server_id=server.server_id
                    )
                    server.resources.append(resource)
                    self._resource_index[resource.uri] = resource
                
                logger.info(f"Discovered {len(server.resources)} resources from {server.name}")
        except Exception as e:
            logger.error(f"Failed to discover resources from {server.name}: {e}")
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_id: Optional[str] = None
    ) -> MCPToolResult:
        """
        Call a tool on an MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_id: Optional server ID (if not provided, searches all servers)
            
        Returns:
            MCPToolResult with execution result
        """
        start_time = asyncio.get_event_loop().time()
        
        # Find the tool
        tool = None
        target_server = None
        
        if server_id:
            tool_key = f"{server_id}:{tool_name}"
            tool = self._tool_index.get(tool_key)
            target_server = self._servers.get(server_id)
        else:
            # Search all servers
            for key, t in self._tool_index.items():
                if t.name == tool_name:
                    tool = t
                    target_server = self._servers.get(t.server_id)
                    break
        
        if not tool or not target_server:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found"
            )
        
        if target_server.status != MCPServerStatus.CONNECTED:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Server '{target_server.name}' is not connected"
            )
        
        try:
            client = await self._get_http_client()
            response = await client.post(
                f"{target_server.url}/mcp/tools/call",
                headers=target_server.headers,
                json={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Check for error in result
                if result_data.get("isError"):
                    return MCPToolResult(
                        tool_name=tool_name,
                        success=False,
                        error=result_data.get("content", "Unknown error"),
                        execution_time_ms=execution_time
                    )
                
                return MCPToolResult(
                    tool_name=tool_name,
                    success=True,
                    result=result_data.get("content"),
                    execution_time_ms=execution_time
                )
            else:
                return MCPToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"Tool call error for {tool_name}: {e}")
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    async def read_resource(
        self,
        uri: str,
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Read a resource from an MCP server.
        
        Args:
            uri: Resource URI
            server_id: Optional server ID
            
        Returns:
            Resource content
        """
        resource = self._resource_index.get(uri)
        
        if not resource and server_id:
            # Try to find on specific server
            server = self._servers.get(server_id)
            if server:
                for r in server.resources:
                    if r.uri == uri:
                        resource = r
                        break
        
        if not resource:
            raise MCPError(f"Resource '{uri}' not found")
        
        target_server = self._servers.get(resource.server_id)
        if not target_server or target_server.status != MCPServerStatus.CONNECTED:
            raise MCPError(f"Server for resource '{uri}' is not connected")
        
        try:
            client = await self._get_http_client()
            response = await client.post(
                f"{target_server.url}/mcp/resources/read",
                headers=target_server.headers,
                json={"uri": uri}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise MCPError(f"Failed to read resource: {response.text}")
                
        except Exception as e:
            logger.error(f"Resource read error for {uri}: {e}")
            raise MCPError(f"Failed to read resource '{uri}': {e}") from e
    
    def get_all_tools(self) -> List[MCPTool]:
        """Get all discovered tools from all servers."""
        return list(self._tool_index.values())
    
    def get_server_tools(self, server_id: str) -> List[MCPTool]:
        """Get tools from a specific server."""
        server = self._servers.get(server_id)
        return server.tools if server else []
    
    def get_all_resources(self) -> List[MCPResource]:
        """Get all discovered resources from all servers."""
        return list(self._resource_index.values())
    
    async def get_server_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific server."""
        server = self._servers.get(server_id)
        if not server:
            return None
        
        return {
            "server_id": server.server_id,
            "name": server.name,
            "url": server.url,
            "status": server.status.value,
            "tool_count": len(server.tools),
            "resource_count": len(server.resources),
            "last_connected": server.last_connected.isoformat() if server.last_connected else None,
            "error_message": server.error_message
        }
    
    async def get_all_status(self) -> List[Dict[str, Any]]:
        """Get status of all registered servers."""
        return [
            await self.get_server_status(sid)
            for sid in self._servers.keys()
        ]
    
    async def disconnect_server(self, server_id: str) -> None:
        """Disconnect from an MCP server."""
        if server_id not in self._servers:
            return
        
        server = self._servers[server_id]
        
        # Remove tools from index
        for tool in server.tools:
            tool_key = f"{server_id}:{tool.name}"
            self._tool_index.pop(tool_key, None)
        
        # Remove resources from index
        for resource in server.resources:
            self._resource_index.pop(resource.uri, None)
        
        server.status = MCPServerStatus.DISCONNECTED
        server.tools = []
        server.resources = []
        
        logger.info(f"Disconnected from MCP server: {server.name}")
    
    async def unregister_server(self, server_id: str) -> None:
        """Unregister and disconnect an MCP server."""
        await self.disconnect_server(server_id)
        self._servers.pop(server_id, None)
        logger.info(f"Unregistered MCP server: {server_id}")
    
    async def refresh_all(self) -> Dict[str, bool]:
        """Refresh connections and capabilities for all servers."""
        results = {}
        for server_id in self._servers:
            results[server_id] = await self.connect_server(server_id)
        return results
    
    async def close(self) -> None:
        """Close all connections and cleanup."""
        for server_id in list(self._servers.keys()):
            await self.disconnect_server(server_id)
        
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create global MCP client."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


# Predefined MCP server configurations
MCP_SERVER_PRESETS = {
    "filesystem": {
        "name": "Filesystem MCP",
        "url": "http://localhost:3001",
        "description": "Access and manipulate files on the local filesystem"
    },
    "github": {
        "name": "GitHub MCP",
        "url": "http://localhost:3002",
        "description": "Interact with GitHub repositories, issues, and pull requests"
    },
    "postgres": {
        "name": "PostgreSQL MCP",
        "url": "http://localhost:3003",
        "description": "Query and manage PostgreSQL databases"
    },
    "stripe": {
        "name": "Stripe MCP",
        "url": "http://localhost:3004",
        "description": "Manage Stripe payments, customers, and subscriptions"
    },
    "slack": {
        "name": "Slack MCP",
        "url": "http://localhost:3005",
        "description": "Send messages and interact with Slack workspaces"
    },
    "openclaw": {
        "name": "OpenClaw Bridge",
        "url": settings.OPENCLAW_BRIDGE_URL,
        "description": "Use the local OpenClaw runtime through the bridge service"
    },
}
