"""
Task data model.

Represents tasks assigned to agents in the BuizSwarm platform.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


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


class TaskPriority(int, Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


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


class TaskResult(BaseModel):
    """Result of task execution."""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    output: Optional[str] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)


class TaskExecutionLog(BaseModel):
    """Log entry for task execution."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "info"  # debug, info, warning, error
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    """
    Task model representing work assigned to agents.
    
    Tasks are the primary unit of work in the BuizSwarm platform.
    They are created by agents (typically CEO) and executed by appropriate agents.
    """
    # Identification
    id: str = Field(default_factory=lambda: str(uuid4()))
    company_id: str
    
    # Task definition
    task_type: TaskType
    title: str
    description: str
    
    # Priority and status
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    
    # Assignment
    created_by: Optional[str] = None  # Agent or user ID
    assigned_to: Optional[str] = None  # Agent ID
    required_capabilities: List[str] = Field(default_factory=list)
    
    # Parameters and context
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Result
    result: Optional[TaskResult] = None
    
    # Retry logic
    retry_count: int = 0
    max_retries: int = 3
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)  # Task IDs
    
    # Execution logs
    execution_logs: List[TaskExecutionLog] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.status == TaskStatus.PENDING
    
    def is_active(self) -> bool:
        """Check if task is currently being executed."""
        return self.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]
    
    def is_complete(self) -> bool:
        """Check if task is complete (success or failure)."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries
    
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        if self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None
    
    def assign(self, agent_id: str) -> None:
        """Assign task to an agent."""
        self.assigned_to = agent_id
        self.status = TaskStatus.ASSIGNED
        self.assigned_at = datetime.utcnow()
    
    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.add_log("info", f"Task started by agent {self.assigned_to}")
    
    def complete(self, result: TaskResult) -> None:
        """Mark task as completed."""
        self.result = result
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        
        if result.success:
            self.add_log("info", "Task completed successfully")
        else:
            self.add_log("error", f"Task failed: {result.error_message}")
    
    def fail(self, error_message: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.result = TaskResult(
            success=False,
            error_message=error_message
        )
        self.add_log("error", f"Task failed: {error_message}")
    
    def retry(self) -> None:
        """Prepare task for retry."""
        if self.can_retry():
            self.retry_count += 1
            self.status = TaskStatus.RETRYING
            self.assigned_to = None
            self.assigned_at = None
            self.started_at = None
            self.completed_at = None
            self.add_log("info", f"Task queued for retry (attempt {self.retry_count + 1})")
    
    def cancel(self, reason: str = "") -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.add_log("warning", f"Task cancelled: {reason}")
    
    def add_log(self, level: str, message: str, **metadata) -> None:
        """Add execution log entry."""
        self.execution_logs.append(TaskExecutionLog(
            level=level,
            message=message,
            metadata=metadata
        ))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return self.model_dump()


class TaskTemplate(BaseModel):
    """Template for creating common tasks."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    task_type: TaskType
    default_priority: TaskPriority = TaskPriority.MEDIUM
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    required_capabilities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# SQLAlchemy model
from sqlalchemy import Column, String, DateTime, Integer, JSON, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TaskDB(Base):
    """SQLAlchemy model for Task."""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False, index=True)
    
    task_type = Column(SQLEnum(TaskType), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    priority = Column(Integer, default=TaskPriority.MEDIUM.value)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    
    created_by = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True, index=True)
    required_capabilities = Column(JSON, default=list)
    
    parameters = Column(JSON, default=dict)
    context = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    result = Column(JSON, nullable=True)
    
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    depends_on = Column(JSON, default=list)
    execution_logs = Column(JSON, default=list)
    
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
