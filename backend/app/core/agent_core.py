"""
Agent Core - Agent lifecycle management, state persistence, and health monitoring.

This module provides the foundational infrastructure for managing AI agents in the
BuizSwarm platform, including registration, state transitions, and inter-agent communication.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, TypeVar
from dataclasses import dataclass, field

import redis.asyncio as redis
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AgentState(str, Enum):
    """Agent lifecycle states."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AgentCapability(str, Enum):
    """Agent capability types."""
    STRATEGIC = "strategic"
    DECISION_MAKING = "decision_making"
    ENGINEERING = "engineering"
    MARKETING = "marketing"
    SUPPORT = "support"
    ANALYSIS = "analysis"
    INFRASTRUCTURE = "infrastructure"
    CONTENT_CREATION = "content_creation"
    COMMUNICATION = "communication"


class AgentMessageType(str, Enum):
    """Types of inter-agent messages."""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    REQUEST_INFO = "request_info"
    PROVIDE_INFO = "provide_info"
    COORDINATE = "coordinate"
    ALERT = "alert"


class AgentMessage(BaseModel):
    """Message passed between agents."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_id: Optional[str] = None  # None = broadcast
    message_type: AgentMessageType
    company_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: int = Field(default=5, ge=1, le=10)
    correlation_id: Optional[str] = None


@dataclass
class AgentMetrics:
    """Runtime metrics for an agent."""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time_ms: float = 0.0
    last_activity: Optional[datetime] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    error_count: int = 0
    messages_sent: int = 0
    messages_received: int = 0


@dataclass  
class AgentContext:
    """Context maintained for each agent instance."""
    agent_id: str
    agent_type: str
    company_id: str
    state: AgentState = AgentState.INITIALIZING
    capabilities: Set[AgentCapability] = field(default_factory=set)
    memory: Dict[str, Any] = field(default_factory=dict)
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_state_change: datetime = field(default_factory=datetime.utcnow)
    current_task_id: Optional[str] = None
    message_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "company_id": self.company_id,
            "state": self.state.value,
            "capabilities": [c.value for c in self.capabilities],
            "memory": self.memory,
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "total_execution_time_ms": self.metrics.total_execution_time_ms,
                "last_activity": self.metrics.last_activity.isoformat() if self.metrics.last_activity else None,
                "error_count": self.metrics.error_count,
                "messages_sent": self.metrics.messages_sent,
                "messages_received": self.metrics.messages_received,
            },
            "created_at": self.created_at.isoformat(),
            "last_state_change": self.last_state_change.isoformat(),
            "current_task_id": self.current_task_id,
        }


class AgentLifecycle:
    """
    Manages the lifecycle of an individual agent.
    
    Handles state transitions, health checks, and graceful shutdown.
    """
    
    # Valid state transitions
    VALID_TRANSITIONS: Dict[AgentState, Set[AgentState]] = {
        AgentState.INITIALIZING: {AgentState.IDLE, AgentState.ERROR},
        AgentState.IDLE: {AgentState.PLANNING, AgentState.EXECUTING, AgentState.SHUTDOWN, AgentState.ERROR},
        AgentState.PLANNING: {AgentState.EXECUTING, AgentState.IDLE, AgentState.ERROR},
        AgentState.EXECUTING: {AgentState.IDLE, AgentState.WAITING, AgentState.ERROR},
        AgentState.WAITING: {AgentState.EXECUTING, AgentState.IDLE, AgentState.ERROR},
        AgentState.ERROR: {AgentState.IDLE, AgentState.SHUTDOWN},
        AgentState.SHUTDOWN: set(),
    }
    
    def __init__(self, context: AgentContext):
        self.context = context
        self._state_lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._message_handler_task: Optional[asyncio.Task] = None
        self._message_handlers: Dict[AgentMessageType, List[Callable[[AgentMessage], Coroutine[Any, Any, None]]]] = {}
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> bool:
        """Initialize the agent lifecycle."""
        try:
            logger.info(f"Initializing agent {self.context.agent_id}")
            await self.transition_to(AgentState.IDLE)
            
            # Start background tasks
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            self._message_handler_task = asyncio.create_task(self._message_handler_loop())
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.context.agent_id}: {e}")
            await self.transition_to(AgentState.ERROR)
            return False
    
    async def transition_to(self, new_state: AgentState) -> bool:
        """Transition agent to a new state."""
        async with self._state_lock:
            current = self.context.state
            
            if new_state not in self.VALID_TRANSITIONS.get(current, set()):
                logger.warning(
                    f"Invalid state transition: {current.value} -> {new_state.value} "
                    f"for agent {self.context.agent_id}"
                )
                return False
            
            logger.info(
                f"Agent {self.context.agent_id} transitioning: "
                f"{current.value} -> {new_state.value}"
            )
            
            self.context.state = new_state
            self.context.last_state_change = datetime.utcnow()
            
            # Persist state change
            await self._persist_state()
            
            return True
    
    async def _persist_state(self) -> None:
        """Persist agent state to Redis."""
        try:
            redis_client = await AgentCore.get_redis()
            key = f"agent:{self.context.agent_id}:state"
            await redis_client.setex(
                key,
                3600,  # 1 hour TTL
                json.dumps(self.context.to_dict())
            )
        except Exception as e:
            logger.error(f"Failed to persist agent state: {e}")
    
    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=30.0  # Check every 30 seconds
                )
            except asyncio.TimeoutError:
                # Perform health check
                is_healthy = await self._perform_health_check()
                if not is_healthy and self.context.state != AgentState.ERROR:
                    logger.warning(f"Agent {self.context.agent_id} health check failed")
                    await self.transition_to(AgentState.ERROR)
    
    async def _perform_health_check(self) -> bool:
        """Perform actual health check."""
        # Check if agent has been stuck in a state too long
        time_in_state = (datetime.utcnow() - self.context.last_state_change).total_seconds()
        
        # If executing for more than 10 minutes, something might be wrong
        if self.context.state == AgentState.EXECUTING and time_in_state > 600:
            logger.warning(f"Agent {self.context.agent_id} executing for {time_in_state}s")
            return False
        
        # If waiting for more than 5 minutes, might be stuck
        if self.context.state == AgentState.WAITING and time_in_state > 300:
            logger.warning(f"Agent {self.context.agent_id} waiting for {time_in_state}s")
            return False
        
        return True
    
    async def _message_handler_loop(self) -> None:
        """Process incoming messages."""
        while not self._shutdown_event.is_set():
            try:
                message = await asyncio.wait_for(
                    self.context.message_queue.get(),
                    timeout=1.0
                )
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error handling message: {e}")
    
    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle a single message."""
        self.context.metrics.messages_received += 1
        
        handlers = self._message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
    
    def register_message_handler(
        self,
        message_type: AgentMessageType,
        handler: Callable[[AgentMessage], Coroutine[Any, Any, None]]
    ) -> None:
        """Register a handler for a specific message type."""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)
    
    async def send_message(self, message: AgentMessage) -> None:
        """Send a message to another agent or broadcast."""
        self.context.metrics.messages_sent += 1
        await AgentCore.route_message(message)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent."""
        logger.info(f"Shutting down agent {self.context.agent_id}")
        self._shutdown_event.set()
        
        await self.transition_to(AgentState.SHUTDOWN)
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._message_handler_task:
            self._message_handler_task.cancel()
            try:
                await self._message_handler_task
            except asyncio.CancelledError:
                pass


class AgentCore:
    """
    Central registry and manager for all agents in the system.
    
    Provides agent registration, discovery, message routing, and global state management.
    """
    
    _instance: Optional['AgentCore'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls) -> 'AgentCore':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._agents: Dict[str, AgentLifecycle] = {}
        self._company_agents: Dict[str, Set[str]] = {}
        self._capability_index: Dict[AgentCapability, Set[str]] = {}
        self._redis: Optional[redis.Redis] = None
        self._initialized = True
        self._message_router_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    @classmethod
    async def get_redis(cls) -> redis.Redis:
        """Get or create Redis connection."""
        instance = cls()
        if instance._redis is None:
            instance._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return instance._redis
    
    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        company_id: str,
        capabilities: List[AgentCapability]
    ) -> AgentLifecycle:
        """Register a new agent with the system."""
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already registered")
        
        context = AgentContext(
            agent_id=agent_id,
            agent_type=agent_type,
            company_id=company_id,
            capabilities=set(capabilities)
        )
        
        lifecycle = AgentLifecycle(context)
        
        # Add to indexes
        self._agents[agent_id] = lifecycle
        
        if company_id not in self._company_agents:
            self._company_agents[company_id] = set()
        self._company_agents[company_id].add(agent_id)
        
        for cap in capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = set()
            self._capability_index[cap].add(agent_id)
        
        # Initialize the agent
        await lifecycle.initialize()
        
        logger.info(f"Registered agent {agent_id} of type {agent_type} for company {company_id}")
        
        return lifecycle
    
    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the system."""
        if agent_id not in self._agents:
            return
        
        lifecycle = self._agents[agent_id]
        context = lifecycle.context
        
        # Shutdown the agent
        await lifecycle.shutdown()
        
        # Remove from indexes
        del self._agents[agent_id]
        
        self._company_agents[context.company_id].discard(agent_id)
        if not self._company_agents[context.company_id]:
            del self._company_agents[context.company_id]
        
        for cap in context.capabilities:
            self._capability_index[cap].discard(agent_id)
            if not self._capability_index[cap]:
                del self._capability_index[cap]
        
        logger.info(f"Unregistered agent {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentLifecycle]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
    
    def get_company_agents(self, company_id: str) -> List[AgentLifecycle]:
        """Get all agents for a company."""
        agent_ids = self._company_agents.get(company_id, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[AgentLifecycle]:
        """Get all agents with a specific capability."""
        agent_ids = self._capability_index.get(capability, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    async def route_message(self, message: AgentMessage) -> None:
        """Route a message to its destination."""
        if message.recipient_id:
            # Direct message
            agent = self._agents.get(message.recipient_id)
            if agent:
                await agent.context.message_queue.put(message)
        else:
            # Broadcast to company agents
            for agent in self.get_company_agents(message.company_id):
                if agent.context.agent_id != message.sender_id:
                    await agent.context.message_queue.put(message)
    
    @classmethod
    async def route_message(cls, message: AgentMessage) -> None:
        """Class method to route messages."""
        instance = cls()
        await instance.route_message(message)
    
    async def broadcast_to_company(
        self,
        company_id: str,
        message_type: AgentMessageType,
        payload: Dict[str, Any],
        sender_id: str,
        priority: int = 5
    ) -> None:
        """Broadcast a message to all agents in a company."""
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=None,  # Broadcast
            message_type=message_type,
            company_id=company_id,
            payload=payload,
            priority=priority
        )
        await self.route_message(message)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        total_agents = len(self._agents)
        state_counts: Dict[str, int] = {}
        
        for lifecycle in self._agents.values():
            state = lifecycle.context.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            "total_agents": total_agents,
            "state_distribution": state_counts,
            "companies_active": len(self._company_agents),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def shutdown_all(self) -> None:
        """Shutdown all agents gracefully."""
        logger.info("Shutting down all agents...")
        
        # Shutdown all agents in parallel
        await asyncio.gather(*[
            lifecycle.shutdown()
            for lifecycle in list(self._agents.values())
        ], return_exceptions=True)
        
        self._agents.clear()
        self._company_agents.clear()
        self._capability_index.clear()
        
        if self._redis:
            await self._redis.close()
        
        logger.info("All agents shutdown complete")


# Global agent core instance
agent_core = AgentCore()
