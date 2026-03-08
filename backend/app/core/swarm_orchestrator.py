"""
Swarm Orchestrator - Multi-agent coordination and daily cycle management.

This module provides the central orchestration logic for coordinating multiple
AI agents across companies, managing daily cycles, task delegation, and
priority queue management.
"""
import asyncio
import heapq
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, IntEnum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple, TypeVar
from uuid import uuid4

import redis.asyncio as redis
from pydantic import BaseModel, Field

from ..config import settings
from .agent_core import (
    AgentCore, AgentLifecycle, AgentMessage, AgentMessageType,
    AgentCapability, AgentState
)
from .bedrock_client import BedrockClient, BedrockMessage

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskPriority(IntEnum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskType(str, Enum):
    """Types of tasks agents can perform."""
    STRATEGIC_PLANNING = "strategic_planning"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEPLOYMENT = "deployment"
    BUG_FIX = "bug_fix"
    MARKETING_CAMPAIGN = "marketing_campaign"
    CONTENT_CREATION = "content_creation"
    CUSTOMER_SUPPORT = "customer_support"
    INFRASTRUCTURE_SETUP = "infrastructure_setup"
    DATA_ANALYSIS = "data_analysis"
    DECISION_MAKING = "decision_making"


@dataclass(order=True)
class PrioritizedTask:
    """Task with priority for queue management."""
    priority: int
    created_at: datetime = field(compare=False)
    task_id: str = field(compare=False)
    task_data: 'Task' = field(compare=False)


class Task(BaseModel):
    """Task definition for agent execution."""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    company_id: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    
    # Assignment
    assigned_agent_id: Optional[str] = None
    required_capabilities: List[AgentCapability] = Field(default_factory=list)
    
    # Content
    title: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_prioritized(self) -> PrioritizedTask:
        """Convert to prioritized task for queue."""
        return PrioritizedTask(
            priority=self.priority.value,
            created_at=self.created_at,
            task_id=self.task_id,
            task_data=self
        )
    
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class DailyCycleReport(BaseModel):
    """Report generated after each daily cycle."""
    company_id: str
    cycle_date: datetime
    cycle_number: int
    
    # Summary
    tasks_completed: int
    tasks_failed: int
    tasks_pending: int
    
    # Performance
    total_execution_time_seconds: float
    revenue_impact: Optional[float] = None
    
    # Decisions
    key_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Issues
    issues_encountered: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Next actions
    planned_actions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Agent activity
    agent_activity: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Generated at
    generated_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class CompanySwarm:
    """Manages the swarm of agents for a single company."""
    company_id: str
    agent_ids: Set[str] = field(default_factory=set)
    task_queue: List[PrioritizedTask] = field(default_factory=list)
    active_tasks: Dict[str, Task] = field(default_factory=dict)
    completed_tasks: List[Task] = field(default_factory=list)
    daily_cycle_count: int = 0
    last_cycle_at: Optional[datetime] = None
    is_cycle_running: bool = False
    
    def __post_init__(self):
        """Initialize heap for task queue."""
        heapq.heapify(self.task_queue)


class SwarmOrchestrator:
    """
    Central orchestrator for multi-agent coordination.
    
    Manages:
    - Daily cycle execution for all companies
    - Task delegation and tracking
    - Agent coordination patterns
    - Priority queue management
    """
    
    def __init__(self):
        self._company_swarms: Dict[str, CompanySwarm] = {}
        self._agent_core = AgentCore()
        self._bedrock = BedrockClient()
        self._redis: Optional[redis.Redis] = None
        
        # Background tasks
        self._daily_cycle_task: Optional[asyncio.Task] = None
        self._task_processor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Task handlers
        self._task_handlers: Dict[TaskType, Callable[[Task], Coroutine[Any, Any, Dict[str, Any]]]] = {}
        
        # Callbacks
        self._cycle_complete_callbacks: List[Callable[[DailyCycleReport], Coroutine[Any, Any, None]]] = []
    
    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        logger.info("Initializing SwarmOrchestrator...")
        
        # Initialize Redis
        self._redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Start background tasks
        self._daily_cycle_task = asyncio.create_task(self._daily_cycle_loop())
        self._task_processor_task = asyncio.create_task(self._task_processor_loop())
        
        logger.info("SwarmOrchestrator initialized")
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis
    
    def register_company(self, company_id: str) -> CompanySwarm:
        """Register a new company for swarm management."""
        if company_id in self._company_swarms:
            return self._company_swarms[company_id]
        
        swarm = CompanySwarm(company_id=company_id)
        self._company_swarms[company_id] = swarm
        
        logger.info(f"Registered company swarm: {company_id}")
        return swarm
    
    def unregister_company(self, company_id: str) -> None:
        """Unregister a company from swarm management."""
        if company_id not in self._company_swarms:
            return
        
        swarm = self._company_swarms[company_id]
        
        # Cancel all pending tasks
        for task in swarm.active_tasks.values():
            task.status = TaskStatus.CANCELLED
        
        del self._company_swarms[company_id]
        logger.info(f"Unregistered company swarm: {company_id}")
    
    def register_agent_with_company(
        self,
        company_id: str,
        agent_id: str,
        capabilities: List[AgentCapability]
    ) -> None:
        """Register an agent with a company swarm."""
        swarm = self._company_swarms.get(company_id)
        if not swarm:
            swarm = self.register_company(company_id)
        
        swarm.agent_ids.add(agent_id)
        logger.info(f"Registered agent {agent_id} with company {company_id}")
    
    def submit_task(self, task: Task) -> str:
        """
        Submit a task to the swarm.
        
        Returns:
            Task ID
        """
        swarm = self._company_swarms.get(task.company_id)
        if not swarm:
            swarm = self.register_company(task.company_id)
        
        # Add to priority queue
        prioritized = task.to_prioritized()
        heapq.heappush(swarm.task_queue, prioritized)
        
        # Persist to Redis
        asyncio.create_task(self._persist_task(task))
        
        logger.info(f"Submitted task {task.task_id} ({task.task_type.value}) for company {task.company_id}")
        
        return task.task_id
    
    async def _persist_task(self, task: Task) -> None:
        """Persist task to Redis."""
        try:
            redis_client = await self._get_redis()
            key = f"task:{task.task_id}"
            await redis_client.setex(
                key,
                86400,  # 24 hour TTL
                task.model_dump_json()
            )
        except Exception as e:
            logger.error(f"Failed to persist task: {e}")
    
    def register_task_handler(
        self,
        task_type: TaskType,
        handler: Callable[[Task], Coroutine[Any, Any, Dict[str, Any]]]
    ) -> None:
        """Register a handler for a specific task type."""
        self._task_handlers[task_type] = handler
        logger.info(f"Registered task handler for {task_type.value}")
    
    def on_cycle_complete(
        self,
        callback: Callable[[DailyCycleReport], Coroutine[Any, Any, None]]
    ) -> None:
        """Register a callback for cycle completion."""
        self._cycle_complete_callbacks.append(callback)
    
    async def _daily_cycle_loop(self) -> None:
        """Main loop for daily cycle execution."""
        while not self._shutdown_event.is_set():
            try:
                now = datetime.utcnow()
                target_hour = settings.AGENT_DAILY_CYCLE_HOUR
                
                # Calculate next cycle time
                if now.hour < target_hour:
                    next_cycle = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
                else:
                    next_cycle = (now + timedelta(days=1)).replace(
                        hour=target_hour, minute=0, second=0, microsecond=0
                    )
                
                wait_seconds = (next_cycle - now).total_seconds()
                
                logger.info(f"Next daily cycle at {next_cycle} (in {wait_seconds/3600:.1f} hours)")
                
                # Wait until next cycle or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=wait_seconds
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    pass  # Time for daily cycle
                
                # Execute daily cycles for all companies
                await self._execute_all_daily_cycles()
                
            except Exception as e:
                logger.error(f"Error in daily cycle loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _execute_all_daily_cycles(self) -> None:
        """Execute daily cycles for all registered companies."""
        logger.info(f"Starting daily cycles for {len(self._company_swarms)} companies")
        
        # Execute cycles in parallel with concurrency limit
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent cycles
        
        async def execute_with_limit(company_id: str):
            async with semaphore:
                await self._execute_company_daily_cycle(company_id)
        
        await asyncio.gather(*[
            execute_with_limit(company_id)
            for company_id in self._company_swarms.keys()
        ], return_exceptions=True)
        
        logger.info("All daily cycles completed")
    
    async def _execute_company_daily_cycle(self, company_id: str) -> None:
        """Execute daily cycle for a single company."""
        swarm = self._company_swarms.get(company_id)
        if not swarm or swarm.is_cycle_running:
            return
        
        swarm.is_cycle_running = True
        swarm.daily_cycle_count += 1
        swarm.last_cycle_at = datetime.utcnow()
        
        try:
            logger.info(f"Starting daily cycle #{swarm.daily_cycle_count} for company {company_id}")
            
            # 1. Trigger CEO agent for strategic planning
            await self._trigger_ceo_cycle(company_id)
            
            # 2. Process any resulting tasks
            await self._process_company_tasks(company_id)
            
            # 3. Generate cycle report
            report = await self._generate_cycle_report(company_id)
            
            # 4. Notify callbacks
            for callback in self._cycle_complete_callbacks:
                try:
                    await callback(report)
                except Exception as e:
                    logger.error(f"Cycle callback error: {e}")
            
            logger.info(f"Completed daily cycle #{swarm.daily_cycle_count} for company {company_id}")
            
        except Exception as e:
            logger.error(f"Error in daily cycle for company {company_id}: {e}")
        finally:
            swarm.is_cycle_running = False
    
    async def _trigger_ceo_cycle(self, company_id: str) -> None:
        """Trigger CEO agent to perform strategic planning."""
        # Find CEO agent for company
        ceo_agent = None
        for agent_id in self._company_swarms[company_id].agent_ids:
            agent = self._agent_core.get_agent(agent_id)
            if agent and AgentCapability.STRATEGIC in agent.context.capabilities:
                ceo_agent = agent
                break
        
        if not ceo_agent:
            logger.warning(f"No CEO agent found for company {company_id}")
            return
        
        # Create strategic planning task
        task = Task(
            company_id=company_id,
            task_type=TaskType.STRATEGIC_PLANNING,
            priority=TaskPriority.HIGH,
            title="Daily Strategic Planning",
            description="Evaluate company state and make strategic decisions",
            required_capabilities=[AgentCapability.STRATEGIC],
            assigned_agent_id=ceo_agent.context.agent_id
        )
        
        self.submit_task(task)
    
    async def _task_processor_loop(self) -> None:
        """Continuously process tasks from queues."""
        while not self._shutdown_event.is_set():
            try:
                # Process tasks for all companies
                for company_id in list(self._company_swarms.keys()):
                    await self._process_company_tasks(company_id)
                
                # Small delay to prevent busy waiting
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(5)
    
    async def _process_company_tasks(self, company_id: str) -> None:
        """Process pending tasks for a company."""
        swarm = self._company_swarms.get(company_id)
        if not swarm:
            return
        
        # Process tasks from queue
        processed = 0
        max_concurrent = settings.AGENT_MAX_CONCURRENT_TASKS
        
        while (swarm.task_queue and 
               len(swarm.active_tasks) < max_concurrent and 
               processed < 5):  # Process max 5 tasks per call
            
            # Get highest priority task
            prioritized = heapq.heappop(swarm.task_queue)
            task = prioritized.task_data
            
            # Check dependencies
            if task.depends_on:
                deps_complete = all(
                    dep_id in [t.task_id for t in swarm.completed_tasks]
                    for dep_id in task.depends_on
                )
                if not deps_complete:
                    # Re-queue with lower priority
                    task.priority = TaskPriority(min(task.priority.value + 1, 5))
                    heapq.heappush(swarm.task_queue, task.to_prioritized())
                    continue
            
            # Assign and execute task
            await self._assign_and_execute_task(task, swarm)
            processed += 1
    
    async def _assign_and_execute_task(self, task: Task, swarm: CompanySwarm) -> None:
        """Assign a task to an agent and execute it."""
        # Find suitable agent
        agent = await self._find_agent_for_task(task, swarm)
        
        if not agent:
            # Re-queue for later
            task.priority = TaskPriority(min(task.priority.value + 1, 5))
            heapq.heappush(swarm.task_queue, task.to_prioritized())
            return
        
        # Assign task
        task.assigned_agent_id = agent.context.agent_id
        task.assigned_at = datetime.utcnow()
        task.status = TaskStatus.ASSIGNED
        
        swarm.active_tasks[task.task_id] = task
        
        # Execute in background
        asyncio.create_task(self._execute_task(task, agent, swarm))
    
    async def _find_agent_for_task(
        self,
        task: Task,
        swarm: CompanySwarm
    ) -> Optional[AgentLifecycle]:
        """Find a suitable agent for a task."""
        # If agent already assigned, use that
        if task.assigned_agent_id:
            return self._agent_core.get_agent(task.assigned_agent_id)
        
        # Find agent with required capabilities
        for agent_id in swarm.agent_ids:
            agent = self._agent_core.get_agent(agent_id)
            if not agent:
                continue
            
            # Check if agent has required capabilities
            if task.required_capabilities:
                has_caps = all(
                    cap in agent.context.capabilities
                    for cap in task.required_capabilities
                )
                if not has_caps:
                    continue
            
            # Check if agent is available
            if agent.context.state == AgentState.IDLE:
                return agent
        
        return None
    
    async def _execute_task(
        self,
        task: Task,
        agent: AgentLifecycle,
        swarm: CompanySwarm
    ) -> None:
        """Execute a task with an agent."""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        
        try:
            # Transition agent to executing
            await agent.transition_to(AgentState.EXECUTING)
            agent.context.current_task_id = task.task_id
            
            # Get task handler
            handler = self._task_handlers.get(task.task_type)
            
            if handler:
                # Execute with timeout
                result = await asyncio.wait_for(
                    handler(task),
                    timeout=settings.AGENT_TASK_TIMEOUT_SECONDS
                )
                task.result = result
                task.status = TaskStatus.COMPLETED
                agent.context.metrics.tasks_completed += 1
            else:
                # No handler - mark as failed
                task.status = TaskStatus.FAILED
                task.error_message = f"No handler registered for task type {task.task_type.value}"
                agent.context.metrics.tasks_failed += 1
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error_message = "Task execution timed out"
            task.retry_count += 1
            agent.context.metrics.tasks_failed += 1
            
            # Retry if under max retries
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.RETRYING
                task.priority = TaskPriority(min(task.priority.value + 1, 5))
                heapq.heappush(swarm.task_queue, task.to_prioritized())
        
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.retry_count += 1
            agent.context.metrics.tasks_failed += 1
            agent.context.metrics.error_count += 1
        
        finally:
            task.completed_at = datetime.utcnow()
            
            # Move from active to completed
            if task.task_id in swarm.active_tasks:
                del swarm.active_tasks[task.task_id]
            
            if task.status == TaskStatus.COMPLETED:
                swarm.completed_tasks.append(task)
            
            # Update agent
            agent.context.current_task_id = None
            await agent.transition_to(AgentState.IDLE)
            agent.context.metrics.last_activity = datetime.utcnow()
            
            # Persist task result
            await self._persist_task(task)
            
            # Notify company agents of completion
            await self._notify_task_complete(task, swarm)
    
    async def _notify_task_complete(self, task: Task, swarm: CompanySwarm) -> None:
        """Notify agents of task completion."""
        message = AgentMessage(
            sender_id="orchestrator",
            message_type=AgentMessageType.TASK_COMPLETE if task.status == TaskStatus.COMPLETED else AgentMessageType.TASK_FAILED,
            company_id=task.company_id,
            payload={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "status": task.status.value,
                "result": task.result,
                "error": task.error_message
            }
        )
        
        await self._agent_core.broadcast_to_company(
            task.company_id,
            message.message_type,
            message.payload,
            "orchestrator"
        )
    
    async def _generate_cycle_report(self, company_id: str) -> DailyCycleReport:
        """Generate report for a completed daily cycle."""
        swarm = self._company_swarms[company_id]
        
        # Calculate metrics
        completed = [t for t in swarm.completed_tasks if t.completed_at and t.completed_at > (swarm.last_cycle_at or datetime.min)]
        failed = [t for t in swarm.completed_tasks if t.status == TaskStatus.FAILED and t.completed_at and t.completed_at > (swarm.last_cycle_at or datetime.min)]
        
        total_time = sum(
            (t.duration_seconds() or 0) for t in completed
        )
        
        # Agent activity
        agent_activity = {}
        for agent_id in swarm.agent_ids:
            agent = self._agent_core.get_agent(agent_id)
            if agent:
                agent_activity[agent_id] = {
                    "type": agent.context.agent_type,
                    "state": agent.context.state.value,
                    "tasks_completed": agent.context.metrics.tasks_completed,
                    "tasks_failed": agent.context.metrics.tasks_failed,
                }
        
        return DailyCycleReport(
            company_id=company_id,
            cycle_date=swarm.last_cycle_at or datetime.utcnow(),
            cycle_number=swarm.daily_cycle_count,
            tasks_completed=len(completed),
            tasks_failed=len(failed),
            tasks_pending=len(swarm.task_queue),
            total_execution_time_seconds=total_time,
            agent_activity=agent_activity
        )
    
    async def get_company_status(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a company's swarm."""
        swarm = self._company_swarms.get(company_id)
        if not swarm:
            return None
        
        return {
            "company_id": company_id,
            "agent_count": len(swarm.agent_ids),
            "pending_tasks": len(swarm.task_queue),
            "active_tasks": len(swarm.active_tasks),
            "completed_tasks": len(swarm.completed_tasks),
            "daily_cycle_count": swarm.daily_cycle_count,
            "last_cycle_at": swarm.last_cycle_at.isoformat() if swarm.last_cycle_at else None,
            "is_cycle_running": swarm.is_cycle_running,
        }
    
    async def get_all_status(self) -> Dict[str, Any]:
        """Get status of all swarms."""
        return {
            "total_companies": len(self._company_swarms),
            "companies": [
                await self.get_company_status(company_id)
                for company_id in self._company_swarms.keys()
            ]
        }
    
    async def trigger_manual_cycle(self, company_id: str) -> bool:
        """Manually trigger a daily cycle for a company."""
        if company_id not in self._company_swarms:
            return False
        
        asyncio.create_task(self._execute_company_daily_cycle(company_id))
        return True
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the orchestrator."""
        logger.info("Shutting down SwarmOrchestrator...")
        self._shutdown_event.set()
        
        # Cancel background tasks
        if self._daily_cycle_task:
            self._daily_cycle_task.cancel()
            try:
                await self._daily_cycle_task
            except asyncio.CancelledError:
                pass
        
        if self._task_processor_task:
            self._task_processor_task.cancel()
            try:
                await self._task_processor_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown all agents
        await self._agent_core.shutdown_all()
        
        if self._redis:
            await self._redis.close()
        
        logger.info("SwarmOrchestrator shutdown complete")


# Global orchestrator instance
_orchestrator: Optional[SwarmOrchestrator] = None


def get_orchestrator() -> SwarmOrchestrator:
    """Get or create global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SwarmOrchestrator()
    return _orchestrator
