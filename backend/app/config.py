"""
Configuration management for BuizSwarm platform.
"""
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_company_profile_manifest() -> str:
    """Resolve the default company profile manifest path for host and container use."""
    explicit = os.environ.get("COMPANY_PROFILE_MANIFEST")
    if explicit:
        return explicit

    candidates = []
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if openclaw_home:
        candidates.append(Path(openclaw_home) / "workspace/projects/profitmax/COMPANY_MANIFEST.json")

    # Host checkout layout:
    # .../profitmax/buiz-swarm/backend/app/config.py -> .../profitmax/COMPANY_MANIFEST.json
    resolved = Path(__file__).resolve()
    if len(resolved.parents) > 3:
        candidates.append(resolved.parents[3] / "COMPANY_MANIFEST.json")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    if candidates:
        return str(candidates[-1])

    return "COMPANY_MANIFEST.json"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "BuizSwarm"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, alias="DEBUG")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    
    # Security
    SECRET_KEY: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/buizswarm",
        alias="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    
    # AWS Bedrock
    AWS_REGION: str = Field(default="us-east-1", alias="AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    AWS_BEARER_TOKEN_BEDROCK: Optional[str] = Field(default=None, alias="AWS_BEARER_TOKEN_BEDROCK")
    BEDROCK_MODEL_ID: str = Field(default="us.anthropic.claude-sonnet-4-6", alias="BEDROCK_MODEL_ID")
    BEDROCK_MAX_TOKENS: int = 4096
    BEDROCK_TEMPERATURE: float = 0.7
    
    # MCP (Model Context Protocol)
    MCP_SERVER_URL: str = Field(default="http://localhost:3000", alias="MCP_SERVER_URL")
    MCP_TIMEOUT_SECONDS: int = 30

    # OpenClaw runtime integration
    OPENCLAW_HOME: str = Field(default="/openclaw", alias="OPENCLAW_HOME")
    OPENCLAW_GATEWAY_URL: str = Field(default="http://host.docker.internal:18789", alias="OPENCLAW_GATEWAY_URL")
    OPENCLAW_GATEWAY_TOKEN: Optional[str] = Field(default=None, alias="OPENCLAW_GATEWAY_TOKEN")
    OPENCLAW_BRIDGE_URL: str = Field(default="http://openclaw-bridge:3006", alias="OPENCLAW_BRIDGE_URL")
    DEFAULT_COMPANY_PROFILE: str = Field(default="profitmax", alias="DEFAULT_COMPANY_PROFILE")
    COMPANY_PROFILE_MANIFEST: str = Field(
        default_factory=_default_company_profile_manifest,
        alias="COMPANY_PROFILE_MANIFEST"
    )
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    STRIPE_PLATFORM_FEE_PERCENT: float = 20.0  # 20% revenue share
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    GITHUB_ORG: Optional[str] = Field(default=None, alias="GITHUB_ORG")
    
    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = Field(default=None, alias="SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL: str = Field(default="noreply@buizswarm.com", alias="SENDGRID_FROM_EMAIL")
    
    # Meta Ads
    META_APP_ID: Optional[str] = Field(default=None, alias="META_APP_ID")
    META_APP_SECRET: Optional[str] = Field(default=None, alias="META_APP_SECRET")
    META_ACCESS_TOKEN: Optional[str] = Field(default=None, alias="META_ACCESS_TOKEN")
    
    # Infrastructure Provisioning
    AWS_INFRA_REGION: str = Field(default="us-west-2", alias="AWS_INFRA_REGION")
    RENDER_API_KEY: Optional[str] = Field(default=None, alias="RENDER_API_KEY")
    NEON_API_KEY: Optional[str] = Field(default=None, alias="NEON_API_KEY")
    
    # Agent Configuration
    AGENT_DAILY_CYCLE_HOUR: int = 9  # 9 AM UTC
    AGENT_MAX_CONCURRENT_TASKS: int = 10
    AGENT_TASK_TIMEOUT_SECONDS: int = 300
    
    # Monitoring
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    SENTRY_DSN: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    
    # Multi-tenancy
    MAX_COMPANIES_PER_USER: int = 10
    MAX_CONCURRENT_COMPANIES: int = 1000
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def database_async_url(self) -> str:
        """Get async database URL."""
        return self.DATABASE_URL.replace(
            "postgresql://", 
            "postgresql+asyncpg://"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
