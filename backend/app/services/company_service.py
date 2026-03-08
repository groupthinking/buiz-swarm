"""
Company Service - Company lifecycle management.

Manages company creation, onboarding, updates, and deletion.
Coordinates with agents and infrastructure services.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..models.company import Company, CompanyStatus, AgentAssignment, InfrastructureConfig
from ..core.agent_core import AgentCapability
from ..core.swarm_orchestrator import get_orchestrator
from ..agents.base_agent import create_agent

logger = logging.getLogger(__name__)


class CompanyService:
    """
    Service for managing company lifecycle.
    
    Handles:
    - Company creation and onboarding
    - Agent assignment and initialization
    - Company updates and configuration
    - Company deletion and cleanup
    """
    
    def __init__(self):
        self._companies: Dict[str, Company] = {}  # In-memory store (replace with DB)
        self._orchestrator = get_orchestrator()
    
    async def create_company(
        self,
        name: str,
        owner_id: str,
        description: Optional[str] = None,
        industry: Optional[str] = None,
        website: Optional[str] = None
    ) -> Company:
        """
        Create a new company.
        
        Args:
            name: Company name
            owner_id: User ID of the owner
            description: Optional company description
            industry: Optional industry
            website: Optional website URL
            
        Returns:
            Created Company instance
        """
        # Generate slug
        slug = self._generate_slug(name)
        
        # Create company
        company = Company(
            name=name,
            slug=slug,
            owner_id=owner_id,
            description=description,
            industry=industry,
            website=website,
            status=CompanyStatus.ONBOARDING
        )
        
        # Store company
        self._companies[company.id] = company
        
        logger.info(f"Created company: {name} ({company.id})")
        
        # Start onboarding
        asyncio.create_task(self._onboard_company(company.id))
        
        return company
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from company name."""
        import re
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while any(c.slug == slug for c in self._companies.values()):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    async def _onboard_company(self, company_id: str) -> None:
        """Run company onboarding process."""
        company = self._companies.get(company_id)
        if not company:
            return
        
        try:
            logger.info(f"Starting onboarding for company {company_id}")
            
            # Step 1: Register with orchestrator
            self._orchestrator.register_company(company_id)
            
            # Step 2: Create and assign agents
            await self._create_company_agents(company)
            
            # Step 3: Provision infrastructure
            await self._provision_infrastructure(company)
            
            # Step 4: Update status
            company.status = CompanyStatus.ACTIVE
            company.status_message = "Company is active and ready"
            
            logger.info(f"Completed onboarding for company {company_id}")
            
        except Exception as e:
            logger.error(f"Onboarding failed for company {company_id}: {e}")
            company.status = CompanyStatus.SUSPENDED
            company.status_message = f"Onboarding failed: {str(e)}"
    
    async def _create_company_agents(self, company: Company) -> None:
        """Create and assign agents for a company."""
        agent_configs = [
            ("ceo", [AgentCapability.STRATEGIC, AgentCapability.ANALYSIS]),
            ("engineering", [AgentCapability.ENGINEERING, AgentCapability.INFRASTRUCTURE]),
            ("marketing", [AgentCapability.MARKETING]),
            ("support", [AgentCapability.SUPPORT]),
        ]
        
        for agent_type, capabilities in agent_configs:
            try:
                # Create agent
                agent = await create_agent(agent_type, company.id)
                
                # Register with orchestrator
                self._orchestrator.register_agent_with_company(
                    company_id=company.id,
                    agent_id=agent.agent_id,
                    capabilities=capabilities
                )
                
                # Add to company
                company.agents.append(AgentAssignment(
                    agent_type=agent_type,
                    agent_id=agent.agent_id,
                    status="active",
                    assigned_at=datetime.utcnow()
                ))
                
                logger.info(f"Created {agent_type} agent for company {company.id}")
                
            except Exception as e:
                logger.error(f"Failed to create {agent_type} agent: {e}")
                company.agents.append(AgentAssignment(
                    agent_type=agent_type,
                    status="error"
                ))
    
    async def _provision_infrastructure(self, company: Company) -> None:
        """Provision infrastructure for a company."""
        # This would integrate with InfrastructureService
        # For now, just set pending status
        company.infrastructure = InfrastructureConfig(
            web_server_status="pending",
            database_status="pending",
            email_status="pending",
            github_status="pending",
            stripe_status="pending"
        )
    
    async def get_company(self, company_id: str) -> Optional[Company]:
        """Get company by ID."""
        return self._companies.get(company_id)
    
    async def get_company_by_slug(self, slug: str) -> Optional[Company]:
        """Get company by slug."""
        for company in self._companies.values():
            if company.slug == slug:
                return company
        return None
    
    async def get_user_companies(self, user_id: str) -> List[Company]:
        """Get all companies owned by or accessible to a user."""
        companies = []
        for company in self._companies.values():
            if company.owner_id == user_id or user_id in company.team_members:
                companies.append(company)
        return companies
    
    async def update_company(
        self,
        company_id: str,
        **updates
    ) -> Optional[Company]:
        """Update company fields."""
        company = self._companies.get(company_id)
        if not company:
            return None
        
        allowed_fields = [
            "name", "description", "industry", "website",
            "settings", "status"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields and hasattr(company, field):
                setattr(company, field, value)
        
        company.updated_at = datetime.utcnow()
        
        logger.info(f"Updated company {company_id}")
        return company
    
    async def delete_company(self, company_id: str) -> bool:
        """Delete a company and cleanup resources."""
        company = self._companies.get(company_id)
        if not company:
            return False
        
        try:
            # Shutdown agents
            for agent_assignment in company.agents:
                if agent_assignment.agent_id:
                    agent = self._orchestrator._agent_core.get_agent(agent_assignment.agent_id)
                    if agent:
                        await agent.shutdown()
            
            # Unregister from orchestrator
            self._orchestrator.unregister_company(company_id)
            
            # Remove from storage
            del self._companies[company_id]
            
            logger.info(f"Deleted company {company_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete company {company_id}: {e}")
            return False
    
    async def trigger_daily_cycle(self, company_id: str) -> bool:
        """Manually trigger daily cycle for a company."""
        company = self._companies.get(company_id)
        if not company or not company.can_run_cycles():
            return False
        
        return await self._orchestrator.trigger_manual_cycle(company_id)
    
    async def get_company_status(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive company status."""
        company = self._companies.get(company_id)
        if not company:
            return None
        
        swarm_status = await self._orchestrator.get_company_status(company_id)
        
        return {
            "company": {
                "id": company.id,
                "name": company.name,
                "slug": company.slug,
                "status": company.status.value,
                "status_message": company.status_message,
                "created_at": company.created_at.isoformat(),
                "daily_cycle_count": company.daily_cycle_count,
                "last_daily_cycle_at": company.last_daily_cycle_at.isoformat() if company.last_daily_cycle_at else None
            },
            "agents": [
                {
                    "type": a.agent_type,
                    "status": a.status,
                    "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
                    "last_activity": a.last_activity.isoformat() if a.last_activity else None
                }
                for a in company.agents
            ],
            "infrastructure": company.infrastructure.model_dump(),
            "metrics": company.metrics.model_dump(),
            "swarm": swarm_status
        }
    
    async def add_team_member(
        self,
        company_id: str,
        user_id: str
    ) -> bool:
        """Add a team member to a company."""
        company = self._companies.get(company_id)
        if not company:
            return False
        
        if user_id not in company.team_members:
            company.team_members.append(user_id)
            company.updated_at = datetime.utcnow()
        
        return True
    
    async def remove_team_member(
        self,
        company_id: str,
        user_id: str
    ) -> bool:
        """Remove a team member from a company."""
        company = self._companies.get(company_id)
        if not company:
            return False
        
        if user_id in company.team_members:
            company.team_members.remove(user_id)
            company.updated_at = datetime.utcnow()
        
        return True
    
    async def pause_company(self, company_id: str) -> bool:
        """Pause a company (stop daily cycles)."""
        company = self._companies.get(company_id)
        if not company:
            return False
        
        company.status = CompanyStatus.PAUSED
        company.status_message = "Company paused by user"
        company.updated_at = datetime.utcnow()
        
        logger.info(f"Paused company {company_id}")
        return True
    
    async def resume_company(self, company_id: str) -> bool:
        """Resume a paused company."""
        company = self._companies.get(company_id)
        if not company:
            return False
        
        company.status = CompanyStatus.ACTIVE
        company.status_message = "Company is active and ready"
        company.updated_at = datetime.utcnow()
        
        logger.info(f"Resumed company {company_id}")
        return True


import asyncio

# Global service instance
_company_service: Optional[CompanyService] = None


def get_company_service() -> CompanyService:
    """Get or create global company service."""
    global _company_service
    if _company_service is None:
        _company_service = CompanyService()
    return _company_service
