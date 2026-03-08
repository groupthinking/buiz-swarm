"""
API Routes - FastAPI endpoints for BuizSwarm platform.

Provides REST API endpoints for:
- Company management
- Agent control
- Task management
- Billing and revenue
- System monitoring
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from pydantic import BaseModel, Field

from ..core.agent_core import AgentCore, AgentState
from ..core.swarm_orchestrator import SwarmOrchestrator, TaskPriority, get_orchestrator
from ..core.bedrock_client import get_bedrock_client
from ..core.mcp_client import get_mcp_client
from ..services.company_service import get_company_service
from ..services.billing_service import get_billing_service
from ..services.infrastructure_service import get_infrastructure_service
from ..models.company import Company, CompanyStatus, CompanySettings
from ..models.task import Task, TaskType

router = APIRouter(prefix="/api/v1")


# ============== Request/Response Models ==============

class CreateCompanyRequest(BaseModel):
    """Request to create a new company."""
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None


class CreateTaskRequest(BaseModel):
    """Request to create a new task."""
    task_type: str
    title: str
    description: str
    priority: str = "medium"
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Request for agent chat."""
    message: str
    agent_type: Optional[str] = None
    session_id: Optional[str] = None


class RevenueRequest(BaseModel):
    """Request to record revenue."""
    amount: float
    source: str
    description: Optional[str] = None


# ============== Company Endpoints ==============

@router.post("/companies", response_model=Dict[str, Any])
async def create_company(
    request: CreateCompanyRequest,
    background_tasks: BackgroundTasks
):
    """Create a new company."""
    service = get_company_service()
    
    # TODO: Get owner_id from authenticated user
    owner_id = "user_123"  # Placeholder
    
    company = await service.create_company(
        name=request.name,
        owner_id=owner_id,
        description=request.description,
        industry=request.industry,
        website=request.website
    )
    
    return {
        "success": True,
        "company": company.model_dump()
    }


@router.get("/companies")
async def list_companies():
    """List all companies for the current user."""
    service = get_company_service()
    
    # TODO: Get user_id from authenticated user
    user_id = "user_123"  # Placeholder
    
    companies = await service.get_user_companies(user_id)
    
    return {
        "companies": [c.model_dump() for c in companies]
    }


@router.get("/companies/{company_id}")
async def get_company(company_id: str):
    """Get company details."""
    service = get_company_service()
    company = await service.get_company(company_id)
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company.model_dump()


@router.get("/companies/{company_id}/status")
async def get_company_status(company_id: str):
    """Get comprehensive company status."""
    service = get_company_service()
    status_data = await service.get_company_status(company_id)
    
    if not status_data:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return status_data


@router.post("/companies/{company_id}/pause")
async def pause_company(company_id: str):
    """Pause a company (stop daily cycles)."""
    service = get_company_service()
    success = await service.pause_company(company_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {"success": True, "message": "Company paused"}


@router.post("/companies/{company_id}/resume")
async def resume_company(company_id: str):
    """Resume a paused company."""
    service = get_company_service()
    success = await service.resume_company(company_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {"success": True, "message": "Company resumed"}


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str):
    """Delete a company."""
    service = get_company_service()
    success = await service.delete_company(company_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {"success": True, "message": "Company deleted"}


# ============== Agent Endpoints ==============

@router.post("/companies/{company_id}/agents/{agent_type}/chat")
async def chat_with_agent(
    company_id: str,
    agent_type: str,
    request: ChatRequest
):
    """Chat with a company agent."""
    orchestrator = get_orchestrator()
    
    # Get company agents
    agents = orchestrator._agent_core.get_company_agents(company_id)
    
    # Find agent of requested type
    target_agent = None
    for agent in agents:
        if agent.context.agent_type == agent_type:
            target_agent = agent
            break
    
    if not target_agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent of type {agent_type} not found for this company"
        )
    
    # Generate response using Bedrock
    bedrock = get_bedrock_client()
    
    from ..core.bedrock_client import BedrockMessage
    messages = [
        BedrockMessage.system(f"You are the {agent_type} agent for this company."),
        BedrockMessage.user(request.message)
    ]
    
    response = await bedrock.generate(
        messages=messages,
        session_id=request.session_id or f"{company_id}:{agent_type}"
    )
    
    return {
        "response": response.content,
        "agent_type": agent_type,
        "session_id": request.session_id
    }


@router.post("/companies/{company_id}/daily-cycle")
async def trigger_daily_cycle(company_id: str):
    """Manually trigger daily cycle for a company."""
    service = get_company_service()
    success = await service.trigger_daily_cycle(company_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Company not found or cannot run cycles"
        )
    
    return {"success": True, "message": "Daily cycle triggered"}


# ============== Task Endpoints ==============

@router.post("/companies/{company_id}/tasks")
async def create_task(
    company_id: str,
    request: CreateTaskRequest
):
    """Create a new task for a company."""
    orchestrator = get_orchestrator()
    
    # Map priority string to enum
    priority_map = {
        "critical": TaskPriority.CRITICAL,
        "high": TaskPriority.HIGH,
        "medium": TaskPriority.MEDIUM,
        "low": TaskPriority.LOW,
        "background": TaskPriority.BACKGROUND
    }
    
    task = Task(
        company_id=company_id,
        task_type=TaskType(request.task_type),
        priority=priority_map.get(request.priority, TaskPriority.MEDIUM),
        title=request.title,
        description=request.description,
        parameters=request.parameters
    )
    
    task_id = orchestrator.submit_task(task)
    
    return {
        "success": True,
        "task_id": task_id,
        "status": "submitted"
    }


@router.get("/companies/{company_id}/tasks")
async def list_company_tasks(company_id: str):
    """List tasks for a company."""
    orchestrator = get_orchestrator()
    swarm = orchestrator._company_swarms.get(company_id)
    
    if not swarm:
        return {"tasks": []}
    
    return {
        "pending_tasks": len(swarm.task_queue),
        "active_tasks": len(swarm.active_tasks),
        "completed_tasks": len(swarm.completed_tasks),
        "tasks": [
            {
                "task_id": t.task_id,
                "type": t.task_type.value,
                "status": t.status.value,
                "title": t.title
            }
            for t in list(swarm.active_tasks.values())
        ]
    }


# ============== Billing Endpoints ==============

@router.post("/companies/{company_id}/revenue")
async def record_revenue(
    company_id: str,
    request: RevenueRequest
):
    """Record revenue for a company."""
    company_service = get_company_service()
    billing_service = get_billing_service()
    
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    transaction = await billing_service.record_revenue(
        company=company,
        amount=request.amount,
        source=request.source,
        description=request.description or ""
    )
    
    return transaction


@router.get("/companies/{company_id}/billing")
async def get_company_billing(company_id: str):
    """Get billing summary for a company."""
    company_service = get_company_service()
    billing_service = get_billing_service()
    
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    summary = await billing_service.get_company_billing_summary(company)
    
    return summary


@router.get("/companies/{company_id}/transactions")
async def get_company_transactions(
    company_id: str,
    limit: int = 100
):
    """Get transactions for a company."""
    company_service = get_company_service()
    billing_service = get_billing_service()
    
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    transactions = await billing_service.get_company_transactions(
        company_id,
        limit=limit
    )
    
    return {"transactions": transactions}


# ============== Infrastructure Endpoints ==============

@router.get("/companies/{company_id}/infrastructure")
async def get_infrastructure(company_id: str):
    """Get infrastructure status for a company."""
    company_service = get_company_service()
    infra_service = get_infrastructure_service()
    
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    status = await infra_service.get_infrastructure_status(company)
    
    return status


@router.post("/companies/{company_id}/infrastructure/provision")
async def provision_infrastructure(company_id: str):
    """Provision infrastructure for a company."""
    company_service = get_company_service()
    infra_service = get_infrastructure_service()
    
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    results = await infra_service.provision_all(company)
    
    return {
        "success": True,
        "results": results
    }


# ============== System Endpoints ==============

@router.get("/system/health")
async def system_health():
    """Get system health status."""
    orchestrator = get_orchestrator()
    agent_core = AgentCore()
    
    agent_health = await agent_core.get_system_health()
    swarm_status = await orchestrator.get_all_status()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": agent_health,
        "swarms": swarm_status
    }


@router.get("/system/mcp-status")
async def mcp_status():
    """Get MCP server status."""
    mcp = get_mcp_client()
    
    status = await mcp.get_all_status()
    
    return {
        "servers": status,
        "total_tools": len(mcp.get_all_tools()),
        "total_resources": len(mcp.get_all_resources())
    }


@router.get("/system/stats")
async def system_stats():
    """Get system statistics."""
    billing_service = get_billing_service()
    
    platform_summary = await billing_service.get_platform_summary()
    
    return {
        "platform": platform_summary,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============== Webhook Endpoints ==============

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks."""
    billing_service = get_billing_service()
    
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    
    result = await billing_service.handle_stripe_webhook(payload, signature)
    
    return result


# ============== Dashboard Endpoints ==============

@router.get("/dashboard/overview")
async def dashboard_overview():
    """Get dashboard overview data."""
    company_service = get_company_service()
    billing_service = get_billing_service()
    orchestrator = get_orchestrator()
    
    # TODO: Get from authenticated user
    user_id = "user_123"
    
    companies = await company_service.get_user_companies(user_id)
    platform_summary = await billing_service.get_platform_summary()
    swarm_status = await orchestrator.get_all_status()
    
    return {
        "companies": {
            "total": len(companies),
            "active": len([c for c in companies if c.is_active()]),
            "list": [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status.value,
                    "revenue": c.total_revenue_processed,
                    "daily_cycles": c.daily_cycle_count
                }
                for c in companies
            ]
        },
        "revenue": {
            "total_gmv": platform_summary.get("total_gmv", 0),
            "platform_revenue": platform_summary.get("total_platform_revenue", 0),
            "active_companies": platform_summary.get("active_companies", 0)
        },
        "agents": swarm_status,
        "timestamp": datetime.utcnow().isoformat()
    }
