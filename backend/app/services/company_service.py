"""
Company Service - Company lifecycle management.

Manages company creation, onboarding, updates, and deletion.
Coordinates with agents and infrastructure services.
"""
import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..models.company import Company, CompanyStatus, AgentAssignment, InfrastructureConfig
from ..core.agent_core import AgentCapability
from ..core.mcp_client import get_mcp_client
from ..core.swarm_orchestrator import Task, TaskType, get_orchestrator
from ..core.company_profile import get_company_profile_manager
from ..agents.base_agent import BaseAgent, TaskContext, create_agent
from ..agents.ceo_agent import get_default_ceo_config
from ..agents.engineering_agent import get_default_engineering_config
from ..agents.marketing_agent import get_default_marketing_config
from ..agents.support_agent import get_default_support_config
from ..config import settings

logger = logging.getLogger(__name__)


DEFAULT_AGENT_CONFIG_BUILDERS = {
    "ceo": get_default_ceo_config,
    "engineering": get_default_engineering_config,
    "marketing": get_default_marketing_config,
    "support": get_default_support_config,
}

TASK_AGENT_FALLBACKS = {
    TaskType.STRATEGIC_PLANNING: "ceo",
    TaskType.CODE_GENERATION: "engineering",
    TaskType.CODE_REVIEW: "engineering",
    TaskType.DEPLOYMENT: "engineering",
    TaskType.BUG_FIX: "engineering",
    TaskType.INFRASTRUCTURE_SETUP: "engineering",
    TaskType.MARKETING_CAMPAIGN: "marketing",
    TaskType.CONTENT_CREATION: "marketing",
    TaskType.CUSTOMER_SUPPORT: "support",
    TaskType.DATA_ANALYSIS: "ceo",
}


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
        self._profile_manager = get_company_profile_manager()
        self._agent_instances: Dict[str, Dict[str, BaseAgent]] = defaultdict(dict)
        self._register_task_handlers()

    def _register_task_handlers(self) -> None:
        """Register task handlers that route work to real company agent instances."""
        for task_type in TaskType:
            self._orchestrator.register_task_handler(task_type, self._handle_task_execution)

    def _build_agent_config(self, agent_type: str, company: Company):
        """Build an agent config with the active company profile overlay applied."""
        builder = DEFAULT_AGENT_CONFIG_BUILDERS[agent_type]
        base_config = builder()
        company_goal = company.metadata.get("goal") or self._profile_manager.load_manifest().get("goal")
        return self._profile_manager.apply_to_agent_config(
            base_config,
            agent_type=agent_type,
            company_name=company.name,
            company_goal=company_goal,
        )

    def _resolve_agent_type_for_task(self, task: Task) -> Optional[str]:
        """Resolve the intended agent type for a task."""
        target_agent_type = task.metadata.get("target_agent_type") or task.parameters.get("agent_type")
        if target_agent_type:
            return target_agent_type

        if task.task_type == TaskType.DECISION_MAKING:
            decision = task.parameters.get("decision", {})
            return decision.get("type")

        return TASK_AGENT_FALLBACKS.get(task.task_type)

    @staticmethod
    def _maybe_parse_json(response: str) -> Optional[Dict[str, Any]]:
        """Best-effort extraction of a JSON object from a model response."""
        text = response.strip()
        candidates = [text]

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidates.append(text[start:end + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _extract_currency_values(raw_value: Any) -> List[float]:
        """Extract numeric currency-like values from freeform text."""
        if raw_value is None:
            return []
        numbers = re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", str(raw_value))
        return [float(number.replace(",", "")) for number in numbers]

    def _run_local_workflow_heuristic(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Produce a deterministic fallback result when models are unavailable."""
        if workflow_id == "lead_qualification":
            score = 4
            pain_points = inputs.get("pain_points") or []
            if isinstance(pain_points, list):
                score += min(len(pain_points), 2)
            budget_values = self._extract_currency_values(inputs.get("budget_signal"))
            if budget_values:
                score += 2 if max(budget_values) >= 3000 else 1
            timeline = str(inputs.get("timeline", "")).lower()
            if any(token in timeline for token in ["30", "this month", "2 week", "urgent"]):
                score += 2
            notes = str(inputs.get("notes", "")).lower()
            if "warm" in notes:
                score += 1
            score = max(1, min(score, 10))

            if score >= 8:
                verdict = "sales_call"
            elif score >= 6:
                verdict = "nurture"
            else:
                verdict = "disqualify"
            if budget_values and max(budget_values) >= 5000 and score >= 8:
                verdict = "proposal"

            company_name = inputs.get("company_name", "the lead")
            contact_name = inputs.get("contact_name", "there")
            next_action = {
                "proposal": "Send a scoped proposal with pricing options and a 30-minute close call.",
                "sales_call": "Book a sales call within 48 hours and confirm current lead volume plus response-time gaps.",
                "nurture": "Send a short discovery reply and gather missing budget, urgency, and process detail.",
                "disqualify": "Keep the lead in nurture and avoid heavy operator time until a stronger buying signal appears.",
            }[verdict]

            return {
                "summary": f"{company_name} looks like a credible service-business lead with revenue pain around missed follow-up and intake gaps.",
                "icp_fit_score": score,
                "qualification_verdict": verdict,
                "key_risks": [
                    "Exact lead volume is unknown.",
                    "Current close rate and team capacity were not provided.",
                ],
                "suggested_next_action": next_action,
                "draft_reply": (
                    f"Hi {contact_name}, thanks for reaching out. Based on what you shared, it sounds like the biggest leak is speed-to-lead and weekend follow-up. "
                    "We can help tighten intake, automate reactivation, and make sure quote requests get touched fast. "
                    "If you can share your current monthly lead volume and who handles follow-up today, I can recommend the fastest path and whether we should jump straight to a scoped proposal or a short working session."
                ),
            }

        if workflow_id == "outbound_personalization":
            company_name = inputs.get("company_name", "the account")
            industry = inputs.get("industry", "the target market")
            target_buyer = inputs.get("target_buyer", "the buyer")
            offer = inputs.get("offer", "the offer")
            pain = inputs.get("pain_hypothesis", "revenue operations are underperforming")
            return {
                "account_brief": f"{company_name} is in {industry} and likely cares about pipeline efficiency, response speed, and revenue predictability.",
                "personalization_angles": [
                    f"Generic outreach is probably suppressing reply rates for {target_buyer}.",
                    f"Slow follow-up can turn high-intent inbound demand into lost pipeline in {industry}.",
                    f"{offer} can be framed as operational leverage rather than another marketing experiment.",
                ],
                "primary_outreach_hook": f"If {company_name} is already generating demand, the fastest revenue gain may be fixing follow-up speed and personalization before buying more top-of-funnel traffic.",
                "cold_email_draft": (
                    f"Subject: Quick idea for {company_name}'s pipeline\n\n"
                    f"I took a look at {company_name} and my guess is the real drag is not demand generation alone, it is how consistently leads are worked once they show interest. "
                    f"We help teams like yours tighten outbound and inbound pipeline ops so follow-up is faster, outreach is more specific, and more conversations convert into revenue. "
                    f"If I mapped the biggest leakage points for {target_buyer}, would you be open to a 15-minute working session next week?"
                ),
                "dm_variant": (
                    f"Likely angle for {company_name}: more revenue from the same pipeline by fixing generic outreach and slow follow-up. "
                    f"If useful, I can send a 3-point teardown for {target_buyer}."
                ),
                "cta": "Offer a short pipeline teardown or working session with one concrete improvement path.",
            }

        if workflow_id == "offer_pricing_review":
            price_values = self._extract_currency_values(inputs.get("current_price"))
            cost_values = self._extract_currency_values(inputs.get("delivery_cost"))
            current_price = max(price_values) if price_values else 0.0
            delivery_cost = max(cost_values) if cost_values else 0.0
            gross_margin = current_price - delivery_cost if current_price else None
            margin_pct = (gross_margin / current_price * 100) if current_price and gross_margin is not None else None
            friction = str(inputs.get("sales_friction", "")).lower()

            verdict = "keep"
            if margin_pct is not None and margin_pct < 60:
                verdict = "raise"
            if "setup fee" in friction or "ramp" in friction:
                verdict = "repackage"

            return {
                "offer_summary": f"{inputs.get('offer_name', 'Offer')} targets {inputs.get('target_customer', 'the current segment')} and is positioned as {inputs.get('market_position', 'premium')}.",
                "pricing_verdict": verdict,
                "margin_snapshot": {
                    "current_price": current_price,
                    "delivery_cost": delivery_cost,
                    "estimated_gross_margin": gross_margin,
                    "estimated_margin_percent": round(margin_pct, 1) if margin_pct is not None else None,
                },
                "risks": [
                    "Setup-fee friction is slowing closes.",
                    "Premium positioning is not yet backed by clear category leadership.",
                ],
                "recommended_changes": [
                    "Shift part of the setup fee into a higher recurring package or milestone-based onboarding.",
                    "Offer a streamlined starter tier with a narrower scope and faster time-to-value.",
                    "Anchor pricing to revenue speed, follow-up automation, and recovered pipeline rather than labor hours.",
                ],
                "test_plan": [
                    "Test one repackaged offer with lower upfront friction.",
                    "Track close rate, cash collected in first 30 days, and fulfillment drag.",
                    "Only raise headline price if the new package holds conversion.",
                ],
                "expected_upside": "Higher first-30-day cash collection and better close-rate if upfront friction is reduced without shrinking scope too far.",
            }

        return None

    async def _handle_task_execution(self, task: Task) -> Dict[str, Any]:
        """Route a task to the correct company agent instance."""
        agent = None

        if task.assigned_agent_id:
            for company_agent in self._agent_instances.get(task.company_id, {}).values():
                if company_agent.agent_id == task.assigned_agent_id:
                    agent = company_agent
                    break

        if agent is None:
            agent_type = self._resolve_agent_type_for_task(task)
            if agent_type:
                agent = self._agent_instances.get(task.company_id, {}).get(agent_type)

        if agent is None:
            return {
                "success": False,
                "error": f"No agent instance available for task {task.task_id}",
            }

        context = TaskContext(
            task_id=task.task_id,
            task_type=task.task_type.value,
            parameters=task.parameters,
            metadata=task.metadata,
        )
        return await agent.execute_task(context)

    async def create_company(
        self,
        name: str,
        owner_id: str,
        description: Optional[str] = None,
        industry: Optional[str] = None,
        website: Optional[str] = None,
        goal: Optional[str] = None,
        profile: Optional[str] = None,
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
            status=CompanyStatus.ONBOARDING,
            metadata={
                "profile": profile or settings.DEFAULT_COMPANY_PROFILE,
                "goal": goal or self._profile_manager.load_manifest().get("goal"),
            }
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
                config = self._build_agent_config(agent_type, company)

                # Create agent
                agent = await create_agent(agent_type, company.id, config=config)
                self._agent_instances[company.id][agent_type] = agent
                
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

    async def get_company_agent(self, company_id: str, agent_type: str) -> Optional[BaseAgent]:
        """Get a live agent instance for a company."""
        return self._agent_instances.get(company_id, {}).get(agent_type)

    async def list_company_workflows(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Return the active workflow library for a company."""
        company = self._companies.get(company_id)
        if not company:
            return None

        return {
            "profile": company.metadata.get("profile"),
            "goal": company.metadata.get("goal"),
            "operator_skills": self._profile_manager.list_operator_skills(),
            "workflows": self._profile_manager.list_workflows(),
        }

    async def run_company_workflow(
        self,
        company_id: str,
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute a configured ProfitMax workflow against the assigned agent."""
        company = self._companies.get(company_id)
        if not company:
            return None

        workflow = self._profile_manager.build_workflow_execution(
            workflow_id=workflow_id,
            company_name=company.name,
            company_goal=company.metadata.get("goal"),
            inputs=inputs,
        )
        if not workflow:
            return {"error": f"Workflow `{workflow_id}` is not defined in the active profile."}

        agent_type = workflow.get("agent_type")
        agent = self._agent_instances.get(company_id, {}).get(agent_type)
        if not agent:
            return {"error": f"Agent `{agent_type}` is not active for company {company_id}."}

        response = await agent.generate_response(workflow["prompt"], use_memory=True)
        execution_backend = "bedrock"
        fallback_result: Optional[Dict[str, Any]] = None
        heuristic_result: Optional[Dict[str, Any]] = None

        if not response or response.startswith("Error:"):
            fallback_result = await self._run_openclaw_workflow_fallback(
                workflow=workflow,
                company=company,
                inputs=inputs or {},
            )
            if fallback_result and fallback_result.get("status") == "ok":
                response = str(fallback_result.get("reply") or fallback_result.get("response") or response)
                execution_backend = "openclaw"
            heuristic_result = self._run_local_workflow_heuristic(workflow_id, inputs or {})
            if heuristic_result and execution_backend != "openclaw":
                response = json.dumps(heuristic_result, indent=2)
                execution_backend = "heuristic"

        return {
            "workflow_id": workflow["workflow_id"],
            "workflow_name": workflow["name"],
            "agent_type": agent_type,
            "task_type": workflow.get("task_type"),
            "execution_backend": execution_backend,
            "operator_skills": workflow.get("operator_skills", {}),
            "response": response,
            "parsed_response": self._maybe_parse_json(response),
            "profile": agent.config.metadata.get("profile"),
            "profile_sources": agent.config.metadata.get("profile_sources", []),
            "openclaw_fallback": fallback_result,
            "heuristic_fallback": heuristic_result,
        }

    async def _run_openclaw_workflow_fallback(
        self,
        workflow: Dict[str, Any],
        company: Company,
        inputs: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Use the OpenClaw bridge when the local model runtime is unavailable."""
        openclaw_agent_id = workflow.get("openclaw_agent_id")
        if not openclaw_agent_id:
            return None

        tool_name = f"openclaw_{openclaw_agent_id}"
        mcp = get_mcp_client()
        result = await mcp.call_tool(
            tool_name,
            {
                "task": workflow["prompt"],
                "context": {
                    "company_id": company.id,
                    "company_name": company.name,
                    "workflow_id": workflow["workflow_id"],
                    "workflow_name": workflow["name"],
                    "inputs": inputs,
                },
                "mode": workflow.get("openclaw_mode", "execute"),
                "timeout_seconds": 20,
            },
        )
        if not result.success:
            return {
                "tool_name": tool_name,
                "status": "error",
                "error": result.error,
            }

        payload = result.result if isinstance(result.result, dict) else {"raw": result.result}
        return {
            "tool_name": tool_name,
            "status": str(payload.get("status") or "ok"),
            "agent_id": payload.get("agent_id"),
            "agent_name": payload.get("agent_name"),
            "reply": payload.get("reply") or payload.get("response", {}).get("text"),
            "result": payload,
        }
    
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
            self._agent_instances.pop(company_id, None)
            
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
                "last_daily_cycle_at": company.last_daily_cycle_at.isoformat() if company.last_daily_cycle_at else None,
                "profile": company.metadata.get("profile"),
                "goal": company.metadata.get("goal"),
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
            "swarm": swarm_status,
            "profile": self._profile_manager.describe(),
            "workflow_library": self._profile_manager.list_workflows(),
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
