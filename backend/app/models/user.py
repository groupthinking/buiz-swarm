"""
User data model.

Represents users of the BuizSwarm platform.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from passlib.context import CryptContext


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User role levels."""
    ADMIN = "admin"
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class UserPreferences(BaseModel):
    """User preferences and settings."""
    # UI preferences
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    
    # Notification preferences
    email_notifications: bool = True
    push_notifications: bool = True
    daily_digest: bool = True
    
    # Dashboard preferences
    default_dashboard: str = "overview"
    favorite_companies: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(extra="allow")


class UserSubscription(BaseModel):
    """User subscription information."""
    plan: str = "free"  # free, starter, pro, enterprise
    status: str = "active"
    
    # Limits
    max_companies: int = 1
    max_agents_per_company: int = 4
    max_monthly_tasks: int = 1000
    
    # Billing
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Dates
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Usage
    tasks_used_this_month: int = 0
    companies_created: int = 0


class User(BaseModel):
    """
    User model representing a platform user.
    
    Users can own companies, be team members, and have different roles.
    """
    # Identification
    id: str = Field(default_factory=lambda: str(uuid4()))
    email: EmailStr
    username: str
    
    # Profile
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Authentication
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    
    # Role
    role: UserRole = UserRole.OWNER
    
    # Preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Subscription
    subscription: UserSubscription = Field(default_factory=UserSubscription)
    
    # Companies
    owned_companies: List[str] = Field(default_factory=list)
    member_companies: List[str] = Field(default_factory=list)
    
    # Security
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    # API
    api_key: Optional[str] = None
    api_key_created_at: Optional[datetime] = None
    
    # OAuth
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    def set_password(self, password: str) -> None:
        """Set user password."""
        self.hashed_password = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify user password."""
        if not self.hashed_password:
            return False
        return pwd_context.verify(password, self.hashed_password)
    
    def record_login(self, ip_address: Optional[str] = None) -> None:
        """Record successful login."""
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def record_failed_login(self) -> None:
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + datetime.timedelta(minutes=30)
    
    def can_create_company(self) -> bool:
        """Check if user can create a new company."""
        total_companies = len(self.owned_companies) + len(self.member_companies)
        return total_companies < self.subscription.max_companies
    
    def get_company_role(self, company_id: str) -> Optional[UserRole]:
        """Get user's role in a company."""
        if company_id in self.owned_companies:
            return UserRole.OWNER
        if company_id in self.member_companies:
            return self.role
        return None
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        role_permissions = {
            UserRole.ADMIN: ["*"],
            UserRole.OWNER: [
                "company:create", "company:delete", "company:update",
                "agent:manage", "billing:manage", "team:manage"
            ],
            UserRole.MEMBER: [
                "company:view", "company:update",
                "agent:view", "task:create"
            ],
            UserRole.VIEWER: [
                "company:view", "agent:view", "task:view"
            ]
        }
        
        permissions = role_permissions.get(self.role, [])
        return "*" in permissions or permission in permissions


class TeamInvitation(BaseModel):
    """Invitation to join a company team."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    company_id: str
    email: EmailStr
    role: UserRole = UserRole.MEMBER
    invited_by: str
    
    token: str = Field(default_factory=lambda: str(uuid4()))
    
    status: str = "pending"  # pending, accepted, declined, expired
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + datetime.timedelta(days=7))
    accepted_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.utcnow() > self.expires_at
    
    def can_accept(self) -> bool:
        """Check if invitation can be accepted."""
        return self.status == "pending" and not self.is_expired()


# SQLAlchemy model
from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserDB(Base):
    """SQLAlchemy model for User."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    role = Column(SQLEnum(UserRole), default=UserRole.OWNER)
    
    preferences = Column(JSON, default=dict)
    subscription = Column(JSON, default=dict)
    
    owned_companies = Column(JSON, default=list)
    member_companies = Column(JSON, default=list)
    
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    api_key = Column(String, nullable=True)
    api_key_created_at = Column(DateTime, nullable=True)
    
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_metadata = Column("metadata", JSON, default=dict)
