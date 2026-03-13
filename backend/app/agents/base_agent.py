"""
Base Agent - Foundation class for all specialized agents.

Provides common functionality for agent initialization, message handling,
LLM interaction, and task execution.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar
from datetime import datetime

from pydantic import BaseModel, Field

from ..core.agent_core import (
    AgentCore, AgentLifecycle, AgentContext, AgentState,
    AgentCapability, AgentMessage, AgentMessageType
)
from ..core.bedrock_client import BedrockClient, BedrockMessage, BedrockTool
from ..core.mcp_client import MCPClient, get_mcp_client
from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    agent_type: str
    capabilities: List[AgentCapability]
    system_prompt: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.7)
    enable_mcp_tools: bool = Field(default=True)
    enable_conversation_memory: bool = Field(default=True)
    auto_execute_tools: bool = Field(default=True)


@dataclass
class TaskContext:
    """Context for task execution."""
    task_id: str
    task_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all agents in the BuizSwarm platform.
    
    Provides:
    - Agent lifecycle management
    - LLM interaction via Bedrock
    - MCP tool integration
    - Message handling
    - Task execution framework
    """
    
    def __init__(
        self,
        agent_id: str,
        company_id: str,
        config: AgentConfig
    ):
        self.agent_id = agent_id
        self.company_id = company_id
        self.config = config
        
        # Core components
        self._agent_core = AgentCore()
        self._bedrock = BedrockClient()
        self._mcp = get_mcp_client()
        
        # Lifecycle
        self._lifecycle: Optional[AgentLifecycle] = None
        
        # Conversation memory
        self._conversation_history: List[BedrockMessage] = []
        
        # Registered tools
        self._tools: Dict[str, BedrockTool] = {}
        
        # Message handlers
        self._message_handlers: Dict[AgentMessageType, List[Callable[[AgentMessage], None]]] = {}
        
        logger.info(f"Initialized {config.agent_type} agent: {agent_id}")
    
    async def initialize(self) -> bool:
        """Initialize the agent and register with the system."""
        try:
            # Register with agent core
            self._lifecycle = await self._agent_core.register_agent(
                agent_id=self.agent_id,
                agent_type=self.config.agent_type,
                company_id=self.company_id,
                capabilities=self.config.capabilities
            )
            
            # Register message handlers
            self._register_message_handlers()
            
            # Register tools
            await self._register_tools()
            
            # Initialize conversation with system prompt
            if self.config.system_prompt:
                self._conversation_history.append(
                    BedrockMessage.system(self.config.system_prompt)
                )
            
            logger.info(f"Agent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_id}: {e}")
            return False
    
    def _register_message_handlers(self) -> None:
        """Register handlers for different message types."""
        if self._lifecycle:
            self._lifecycle.register_message_handler(
                AgentMessageType.TASK_ASSIGNMENT,
                self._on_task_assignment
            )
            self._lifecycle.register_message_handler(
                AgentMessageType.REQUEST_INFO,
                self._on_request_info
            )
            self._lifecycle.register_message_handler(
                AgentMessageType.COORDINATE,
                self._on_coordinate
            )
    
    async def _register_tools(self) -> None:
        """Register tools with Bedrock client."""
        # Override in subclasses to register specific tools
        pass
    
    def register_tool(self, tool: BedrockTool) -> None:
        """Register a tool for this agent."""
        self._tools[tool.name] = tool
        self._bedrock.register_tool(tool)
        logger.debug(f"Agent {self.agent_id} registered tool: {tool.name}")
    
    async def generate_response(
        self,
        prompt: str,
        use_memory: bool = True,
        execute_tools: Optional[bool] = None
    ) -> str:
        """
        Generate a response using Claude.
        
        Args:
            prompt: User prompt
            use_memory: Whether to include conversation history
            execute_tools: Whether to auto-execute tools (defaults to config)
            
        Returns:
            Generated response text
        """
        messages = []
        
        if use_memory and self.config.enable_conversation_memory:
            messages.extend(self._conversation_history)
        else:
            # Just use system prompt
            if self.config.system_prompt:
                messages.append(BedrockMessage.system(self.config.system_prompt))
        
        messages.append(BedrockMessage.user(prompt))
        
        should_execute = execute_tools if execute_tools is not None else self.config.auto_execute_tools
        
        try:
            if should_execute and self._tools:
                response = await self._bedrock.execute_with_tools(
                    messages=messages,
                    session_id=f"{self.agent_id}:{self.company_id}"
                )
            else:
                response = await self._bedrock.generate(
                    messages=messages,
                    session_id=f"{self.agent_id}:{self.company_id}"
                )
            
            # Update conversation history
            if use_memory and self.config.enable_conversation_memory:
                self._conversation_history.append(BedrockMessage.user(prompt))
                self._conversation_history.append(BedrockMessage.assistant(response.content))
                
                # Trim history if too long
                self._trim_conversation_history()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: {str(e)}"
    
    async def generate_stream(
        self,
        prompt: str,
        use_memory: bool = True
    ):
        """Generate a streaming response."""
        messages = []
        
        if use_memory and self.config.enable_conversation_memory:
            messages.extend(self._conversation_history)
        else:
            if self.config.system_prompt:
                messages.append(BedrockMessage.system(self.config.system_prompt))
        
        messages.append(BedrockMessage.user(prompt))
        
        async for chunk in self._bedrock.generate_stream(messages):
            yield chunk
    
    def _trim_conversation_history(self, max_messages: int = 20) -> None:
        """Trim conversation history to prevent token overflow."""
        # Keep system message and recent messages
        system_messages = [m for m in self._conversation_history if m.role == "system"]
        other_messages = [m for m in self._conversation_history if m.role != "system"]
        
        if len(other_messages) > max_messages:
            other_messages = other_messages[-max_messages:]
        
        self._conversation_history = system_messages + other_messages
    
    async def execute_task(self, task_context: TaskContext) -> Dict[str, Any]:
        """
        Execute a task. Override in subclasses.
        
        Args:
            task_context: Context for the task
            
        Returns:
            Task result dictionary
        """
        # Base implementation - subclasses should override
        return {
            "success": False,
            "error": "Task execution not implemented in base agent"
        }
    
    async def send_message(
        self,
        message_type: AgentMessageType,
        payload: Dict[str, Any],
        recipient_id: Optional[str] = None
    ) -> None:
        """Send a message to other agents."""
        if self._lifecycle:
            message = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                message_type=message_type,
                company_id=self.company_id,
                payload=payload
            )
            await self._lifecycle.send_message(message)
    
    async def broadcast(
        self,
        message_type: AgentMessageType,
        payload: Dict[str, Any]
    ) -> None:
        """Broadcast a message to all company agents."""
        await self.send_message(message_type, payload, recipient_id=None)
    
    async def _on_task_assignment(self, message: AgentMessage) -> None:
        """Handle task assignment messages."""
        payload = message.payload
        task_id = payload.get("task_id")
        task_type = payload.get("task_type")
        parameters = payload.get("parameters", {})
        
        logger.info(f"Agent {self.agent_id} received task assignment: {task_id}")
        
        task_context = TaskContext(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters
        )
        
        try:
            result = await self.execute_task(task_context)
            
            # Send completion message
            await self.send_message(
                AgentMessageType.TASK_COMPLETE,
                {
                    "task_id": task_id,
                    "result": result,
                    "agent_id": self.agent_id
                },
                recipient_id=message.sender_id
            )
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            
            await self.send_message(
                AgentMessageType.TASK_FAILED,
                {
                    "task_id": task_id,
                    "error": str(e),
                    "agent_id": self.agent_id
                },
                recipient_id=message.sender_id
            )
    
    async def _on_request_info(self, message: AgentMessage) -> None:
        """Handle information request messages."""
        # Override in subclasses
        pass
    
    async def _on_coordinate(self, message: AgentMessage) -> None:
        """Handle coordination messages."""
        # Override in subclasses
        pass
    
    async def use_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool via MCP."""
        if not self.config.enable_mcp_tools:
            return {"error": "MCP tools disabled"}
        
        try:
            result = await self._mcp.call_tool(tool_name, arguments)
            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms
            }
        except Exception as e:
            logger.error(f"MCP tool error: {e}")
            return {"success": False, "error": str(e)}
    
    async def read_mcp_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource via MCP."""
        if not self.config.enable_mcp_tools:
            return {"error": "MCP tools disabled"}
        
        try:
            return await self._mcp.read_resource(uri)
        except Exception as e:
            logger.error(f"MCP resource error: {e}")
            return {"error": str(e)}
    
    def get_state(self) -> AgentState:
        """Get current agent state."""
        if self._lifecycle:
            return self._lifecycle.context.state
        return AgentState.INITIALIZING
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        if self._lifecycle:
            m = self._lifecycle.context.metrics
            return {
                "tasks_completed": m.tasks_completed,
                "tasks_failed": m.tasks_failed,
                "messages_sent": m.messages_sent,
                "messages_received": m.messages_received,
                "error_count": m.error_count,
                "last_activity": m.last_activity.isoformat() if m.last_activity else None
            }
        return {}
    
    async def shutdown(self) -> None:
        """Shutdown the agent."""
        if self._lifecycle:
            await self._lifecycle.shutdown()
        logger.info(f"Agent {self.agent_id} shutdown complete")


# Factory function for creating agents
async def create_agent(
    agent_type: str,
    company_id: str,
    config: Optional[AgentConfig] = None
) -> BaseAgent:
    """
    Factory function to create agents by type.
    
    Args:
        agent_type: Type of agent to create
        company_id: Company ID
        config: Optional custom config
        
    Returns:
        Initialized agent instance
    """
    from .ceo_agent import CEOAgent
    from .engineering_agent import EngineeringAgent
    from .marketing_agent import MarketingAgent
    from .support_agent import SupportAgent
    
    agent_id = f"{agent_type}_{company_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    agent_map = {
        "ceo": CEOAgent,
        "engineering": EngineeringAgent,
        "marketing": MarketingAgent,
        "support": SupportAgent,
    }
    
    agent_class = agent_map.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    agent = agent_class(agent_id, company_id, config)
    await agent.initialize()
    
    return agent
