"""
Company data model.

Represents a company managed by the BuizSwarm platform.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class CompanyStatus(str, Enum):
    """Company lifecycle status."""
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class CompanySettings(BaseModel):
    """Company-specific settings."""
    # Agent configuration
    auto_run_daily_cycles: bool = True
    daily_cycle_hour: int = 9  # UTC hour
    
    # Notification settings
    notify_on_task_complete: bool = True
    notify_on_error: bool = True
    notification_email: Optional[str] = None
    
    # Feature toggles
    enable_marketing: bool = True
    enable_support: bool = True
    enable_engineering: bool = True
    
    # Budget settings
    monthly_ad_budget: float = 500.0
    max_daily_spend: float = 50.0
    
    # Content settings
    content_tone: str = "professional"
    target_audience: str = ""
    
    model_config = ConfigDict(extra="allow")


class CompanyMetrics(BaseModel):
    """Company performance metrics."""
    # Revenue
    total_revenue: float = 0.0
    monthly_recurring_revenue: float = 0.0
    revenue_this_month: float = 0.0
    revenue_last_month: float = 0.0
    
    # Customers
    total_customers: int = 0
    new_customers_this_month: int = 0
    churned_customers_this_month: int = 0
    customer_lifetime_value: float = 0.0
    
    # Marketing
    total_leads: int = 0
    conversion_rate: float = 0.0
    cost_per_acquisition: float = 0.0
    
    # Support
    total_tickets: int = 0
    open_tickets: int = 0
    avg_resolution_time_hours: float = 0.0
    customer_satisfaction_score: float = 0.0
    
    # Product
    total_deployments: int = 0
    uptime_percentage: float = 100.0
    
    # Updated at
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class InfrastructureConfig(BaseModel):
    """Infrastructure configuration for a company."""
    # Web server
    web_server_provider: Optional[str] = None  # "render", "aws", "vercel"
    web_server_url: Optional[str] = None
    web_server_status: str = "not_provisioned"
    
    # Database
    database_provider: Optional[str] = None  # "neon", "aws_rds", "supabase"
    database_url: Optional[str] = None
    database_status: str = "not_provisioned"
    
    # Email
    email_provider: Optional[str] = None  # "sendgrid", "aws_ses"
    email_domain: Optional[str] = None
    email_status: str = "not_provisioned"
    
    # GitHub
    github_repo: Optional[str] = None
    github_org: Optional[str] = None
    github_status: str = "not_provisioned"
    
    # Stripe
    stripe_account_id: Optional[str] = None
    stripe_status: str = "not_provisioned"
    
    # Domain
    domain_name: Optional[str] = None
    dns_status: str = "not_configured"
    
    # SSL
    ssl_certificate: Optional[str] = None
    ssl_expiry: Optional[datetime] = None


class AgentAssignment(BaseModel):
    """Agent assignment for a company."""
    agent_type: str
    agent_id: Optional[str] = None
    status: str = "pending"  # pending, assigned, active, error
    assigned_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class Company(BaseModel):
    """
    Company model representing a business managed by BuizSwarm.
    
    This is the central entity that owns agents, tasks, and all company data.
    """
    # Identification
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    slug: str = Field(..., description="URL-friendly company name")
    
    # Ownership
    owner_id: str
    team_members: List[str] = Field(default_factory=list)
    
    # Status
    status: CompanyStatus = CompanyStatus.ONBOARDING
    status_message: Optional[str] = None
    
    # Configuration
    settings: CompanySettings = Field(default_factory=CompanySettings)
    
    # Business info
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    
    # Metrics
    metrics: CompanyMetrics = Field(default_factory=CompanyMetrics)
    
    # Infrastructure
    infrastructure: InfrastructureConfig = Field(default_factory=InfrastructureConfig)
    
    # Agent assignments
    agents: List[AgentAssignment] = Field(default_factory=list)
    
    # Billing
    revenue_share_percent: float = 20.0  # Platform takes 20%
    total_revenue_processed: float = 0.0
    platform_fees_paid: float = 0.0
    
    # Daily cycles
    daily_cycle_count: int = 0
    last_daily_cycle_at: Optional[datetime] = None
    next_daily_cycle_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    def is_active(self) -> bool:
        """Check if company is active."""
        return self.status == CompanyStatus.ACTIVE
    
    def can_run_cycles(self) -> bool:
        """Check if company can run daily cycles."""
        return self.status in [CompanyStatus.ACTIVE, CompanyStatus.ONBOARDING]
    
    def get_agent(self, agent_type: str) -> Optional[AgentAssignment]:
        """Get agent assignment by type."""
        for agent in self.agents:
            if agent.agent_type == agent_type:
                return agent
        return None
    
    def update_metrics(self, **kwargs) -> None:
        """Update company metrics."""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
        self.metrics.updated_at = datetime.utcnow()
    
    def calculate_platform_fee(self, revenue: float) -> float:
        """Calculate platform fee for given revenue."""
        return revenue * (self.revenue_share_percent / 100)
    
    def record_revenue(self, amount: float) -> Dict[str, float]:
        """Record revenue and calculate fees."""
        platform_fee = self.calculate_platform_fee(amount)
        net_revenue = amount - platform_fee
        
        self.total_revenue_processed += amount
        self.platform_fees_paid += platform_fee
        
        return {
            "gross_revenue": amount,
            "platform_fee": platform_fee,
            "net_revenue": net_revenue
        }


# SQLAlchemy model for database (if using SQLAlchemy)
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CompanyDB(Base):
    """SQLAlchemy model for Company."""
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    owner_id = Column(String, nullable=False, index=True)
    team_members = Column(JSON, default=list)
    
    status = Column(SQLEnum(CompanyStatus), default=CompanyStatus.ONBOARDING)
    status_message = Column(String, nullable=True)
    
    settings = Column(JSON, default=dict)
    description = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    metrics = Column(JSON, default=dict)
    infrastructure = Column(JSON, default=dict)
    agents = Column(JSON, default=list)
    
    revenue_share_percent = Column(Float, default=20.0)
    total_revenue_processed = Column(Float, default=0.0)
    platform_fees_paid = Column(Float, default=0.0)
    
    daily_cycle_count = Column(Integer, default=0)
    last_daily_cycle_at = Column(DateTime, nullable=True)
    next_daily_cycle_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    company_metadata = Column("metadata", JSON, default=dict)
