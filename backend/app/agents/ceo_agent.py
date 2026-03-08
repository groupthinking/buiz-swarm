"""
CEO Agent - Strategic decision maker and company orchestrator.

The CEO Agent is responsible for:
- Business state evaluation
- Strategic decision making
- Task prioritization
- Daily planning and reporting
- Coordinating other agents
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentConfig, TaskContext
from ..core.agent_core import AgentCapability, AgentMessageType
from ..core.bedrock_client import BedrockTool, BedrockMessage
from ..core.swarm_orchestrator import Task, TaskType, TaskPriority

logger = logging.getLogger(__name__)


# System prompt for CEO Agent
CEO_SYSTEM_PROMPT = """You are the CEO Agent of an autonomous AI company. Your role is to:

1. EVALUATE the current state of the business
2. MAKE strategic decisions to grow the company
3. PRIORITIZE tasks based on business impact
4. COORDINATE other agents (Engineering, Marketing, Support)
5. PLAN daily actions and set company direction

Guidelines:
- Always think about revenue growth and customer satisfaction
- Balance short-term wins with long-term strategy
- Delegate technical tasks to Engineering, marketing to Marketing, support to Support
- Make data-driven decisions when possible
- Be decisive but adaptable

When making decisions, consider:
- Current revenue and growth trajectory
- Customer feedback and support tickets
- Technical debt and infrastructure needs
- Marketing opportunities and campaign performance
- Competitive landscape and market trends

Output your decisions in a structured format that can be executed by other agents.
"""


def get_default_ceo_config() -> AgentConfig:
    """Get default configuration for CEO Agent."""
    return AgentConfig(
        agent_type="ceo",
        capabilities=[
            AgentCapability.STRATEGIC,
            AgentCapability.ANALYSIS,
            AgentCapability.DECISION_MAKING
        ],
        system_prompt=CEO_SYSTEM_PROMPT,
        max_tokens=4096,
        temperature=0.7,
        enable_mcp_tools=True,
        enable_conversation_memory=True,
        auto_execute_tools=True
    )


class CEOAgent(BaseAgent):
    """
    CEO Agent for strategic company management.
    
    Makes high-level decisions, evaluates business state, and coordinates
    other agents to achieve company goals.
    """
    
    def __init__(
        self,
        agent_id: str,
        company_id: str,
        config: Optional[AgentConfig] = None
    ):
        if config is None:
            config = get_default_ceo_config()
        
        super().__init__(agent_id, company_id, config)
        
        # Business state tracking
        self._business_state: Dict[str, Any] = {}
        self._daily_goals: List[Dict[str, Any]] = []
        self._decision_history: List[Dict[str, Any]] = []
    
    async def _register_tools(self) -> None:
        """Register CEO-specific tools."""
        # Tool: Evaluate business state
        self.register_tool(BedrockTool(
            name="evaluate_business_state",
            description="Evaluate the current state of the business across all dimensions",
            input_schema={
                "type": "object",
                "properties": {
                    "dimensions": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["revenue", "customers", "product", "marketing", "support"]
                        },
                        "description": "Business dimensions to evaluate"
                    }
                },
                "required": ["dimensions"]
            },
            handler=self._tool_evaluate_business_state
        ))
        
        # Tool: Create task for other agents
        self.register_tool(BedrockTool(
            name="delegate_task",
            description="Create and delegate a task to another agent",
            input_schema={
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": ["engineering", "marketing", "support"],
                        "description": "Type of agent to delegate to"
                    },
                    "task_type": {
                        "type": "string",
                        "description": "Type of task to perform"
                    },
                    "title": {
                        "type": "string",
                        "description": "Task title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed task description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "background"],
                        "description": "Task priority"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Additional task parameters"
                    }
                },
                "required": ["agent_type", "task_type", "title", "description"]
            },
            handler=self._tool_delegate_task
        ))
        
        # Tool: Set company goal
        self.register_tool(BedrockTool(
            name="set_company_goal",
            description="Set a strategic goal for the company",
            input_schema={
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "The strategic goal"
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "quarterly"],
                        "description": "Goal timeframe"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Success metrics"
                    }
                },
                "required": ["goal", "timeframe"]
            },
            handler=self._tool_set_company_goal
        ))
        
        # Tool: Request information from other agents
        self.register_tool(BedrockTool(
            name="request_agent_info",
            description="Request information from another agent",
            input_schema={
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": ["engineering", "marketing", "support"],
                        "description": "Agent type to request info from"
                    },
                    "query": {
                        "type": "string",
                        "description": "Information request"
                    }
                },
                "required": ["agent_type", "query"]
            },
            handler=self._tool_request_agent_info
        ))
    
    async def execute_daily_cycle(self) -> Dict[str, Any]:
        """
        Execute the daily strategic cycle.
        
        This is the main entry point for CEO agent's daily activities.
        """
        logger.info(f"CEO Agent {self.agent_id} starting daily cycle")
        
        # Step 1: Gather information from all agents
        company_status = await self._gather_company_status()
        
        # Step 2: Evaluate business state
        business_evaluation = await self._evaluate_business(company_status)
        
        # Step 3: Make strategic decisions
        decisions = await self._make_strategic_decisions(business_evaluation)
        
        # Step 4: Create and delegate tasks
        delegated_tasks = await self._delegate_strategic_tasks(decisions)
        
        # Step 5: Set daily goals
        goals = await self._set_daily_goals(decisions)
        
        # Step 6: Generate daily report
        report = await self._generate_daily_report(
            company_status,
            business_evaluation,
            decisions,
            delegated_tasks,
            goals
        )
        
        logger.info(f"CEO Agent {self.agent_id} completed daily cycle")
        
        return {
            "success": True,
            "cycle_completed": True,
            "report": report,
            "decisions_made": len(decisions),
            "tasks_delegated": len(delegated_tasks),
            "goals_set": len(goals)
        }
    
    async def _gather_company_status(self) -> Dict[str, Any]:
        """Gather status information from all company systems."""
        # This would integrate with company data sources
        # For now, return template structure
        return {
            "revenue": {
                "current_month": 0,
                "previous_month": 0,
                "growth_rate": 0
            },
            "customers": {
                "total": 0,
                "new_this_month": 0,
                "churn_rate": 0
            },
            "product": {
                "status": "operational",
                "open_issues": 0,
                "recent_deployments": []
            },
            "marketing": {
                "active_campaigns": 0,
                "leads_generated": 0,
                "conversion_rate": 0
            },
            "support": {
                "open_tickets": 0,
                "avg_response_time": 0,
                "satisfaction_score": 0
            }
        }
    
    async def _evaluate_business(self, company_status: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the business state using LLM."""
        prompt = f"""Evaluate the following business state and provide a comprehensive assessment:

Company Status:
{json.dumps(company_status, indent=2)}

Provide your evaluation in this JSON format:
{{
    "overall_health": "excellent|good|fair|poor",
    "key_strengths": ["strength1", "strength2"],
    "key_concerns": ["concern1", "concern2"],
    "priority_areas": ["area1", "area2"],
    "recommendations": ["recommendation1", "recommendation2"]
}}
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            # Extract JSON from response
            evaluation = json.loads(response)
            return evaluation
        except json.JSONDecodeError:
            logger.warning("Failed to parse business evaluation as JSON")
            return {
                "overall_health": "unknown",
                "key_strengths": [],
                "key_concerns": ["Unable to parse evaluation"],
                "priority_areas": [],
                "recommendations": []
            }
    
    async def _make_strategic_decisions(self, evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make strategic decisions based on business evaluation."""
        prompt = f"""Based on this business evaluation, make strategic decisions for today:

Evaluation:
{json.dumps(evaluation, indent=2)}

Make decisions in this JSON format:
{{
    "decisions": [
        {{
            "type": "engineering|marketing|support|general",
            "action": "specific action to take",
            "rationale": "why this decision was made",
            "expected_impact": "high|medium|low",
            "resources_needed": ["resource1", "resource2"]
        }}
    ]
}}
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            decisions_data = json.loads(response)
            decisions = decisions_data.get("decisions", [])
            
            # Store in history
            self._decision_history.extend(decisions)
            
            return decisions
        except json.JSONDecodeError:
            logger.warning("Failed to parse decisions as JSON")
            return []
    
    async def _delegate_strategic_tasks(self, decisions: List[Dict[str, Any]]) -> List[str]:
        """Delegate tasks based on strategic decisions."""
        delegated = []
        
        for decision in decisions:
            agent_type = decision.get("type")
            
            if agent_type in ["engineering", "marketing", "support"]:
                # Create task for the appropriate agent
                task = Task(
                    company_id=self.company_id,
                    task_type=TaskType.DECISION_MAKING,
                    priority=TaskPriority.HIGH,
                    title=decision.get("action", "Strategic task"),
                    description=decision.get("rationale", ""),
                    parameters={
                        "decision": decision,
                        "expected_impact": decision.get("expected_impact", "medium")
                    },
                    metadata={"source": "ceo_daily_cycle"}
                )
                
                # Submit to orchestrator
                from ..core.swarm_orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                task_id = orchestrator.submit_task(task)
                delegated.append(task_id)
        
        return delegated
    
    async def _set_daily_goals(self, decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Set goals for the day based on decisions."""
        goals = []
        
        for decision in decisions:
            if decision.get("expected_impact") in ["high", "medium"]:
                goal = {
                    "description": decision.get("action"),
                    "agent_type": decision.get("type"),
                    "target_date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "status": "pending"
                }
                goals.append(goal)
        
        self._daily_goals = goals
        return goals
    
    async def _generate_daily_report(
        self,
        status: Dict[str, Any],
        evaluation: Dict[str, Any],
        decisions: List[Dict[str, Any]],
        delegated: List[str],
        goals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a comprehensive daily report."""
        return {
            "date": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "company_id": self.company_id,
            "summary": {
                "business_health": evaluation.get("overall_health", "unknown"),
                "decisions_made": len(decisions),
                "tasks_delegated": len(delegated),
                "goals_set": len(goals)
            },
            "evaluation": evaluation,
            "decisions": decisions,
            "delegated_tasks": delegated,
            "daily_goals": goals,
            "next_actions": [
                "Monitor task progress",
                "Review agent reports",
                "Adjust priorities as needed"
            ]
        }
    
    async def execute_task(self, task_context: TaskContext) -> Dict[str, Any]:
        """Execute a task assigned to the CEO agent."""
        task_type = task_context.task_type
        
        if task_type == TaskType.STRATEGIC_PLANNING.value:
            return await self.execute_daily_cycle()
        
        elif task_type == TaskType.DECISION_MAKING.value:
            # Handle specific decision-making task
            decision_params = task_context.parameters.get("decision", {})
            return {
                "success": True,
                "decision_processed": True,
                "decision": decision_params
            }
        
        elif task_type == TaskType.DATA_ANALYSIS.value:
            # Analyze data and provide insights
            data = task_context.parameters.get("data", {})
            analysis = await self._analyze_data(data)
            return {
                "success": True,
                "analysis": analysis
            }
        
        else:
            return await super().execute_task(task_context)
    
    async def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business data and provide insights."""
        prompt = f"""Analyze the following business data and provide insights:

Data:
{json.dumps(data, indent=2)}

Provide analysis in JSON format with insights, trends, and recommendations.
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"insights": response, "parsed": False}
    
    # Tool handlers
    async def _tool_evaluate_business_state(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Evaluate business state."""
        dimensions = args.get("dimensions", [])
        status = await self._gather_company_status()
        
        evaluation = {}
        for dim in dimensions:
            if dim in status:
                evaluation[dim] = status[dim]
        
        return {"evaluation": evaluation}
    
    async def _tool_delegate_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Delegate task to another agent."""
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
            "background": TaskPriority.BACKGROUND
        }
        
        task = Task(
            company_id=self.company_id,
            task_type=TaskType(args.get("task_type", "decision_making")),
            priority=priority_map.get(args.get("priority", "medium"), TaskPriority.MEDIUM),
            title=args.get("title", "Delegated task"),
            description=args.get("description", ""),
            parameters=args.get("parameters", {}),
            metadata={"delegated_by": self.agent_id}
        )
        
        from ..core.swarm_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        task_id = orchestrator.submit_task(task)
        
        return {"task_id": task_id, "status": "submitted"}
    
    async def _tool_set_company_goal(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Set company goal."""
        goal = {
            "goal": args.get("goal"),
            "timeframe": args.get("timeframe"),
            "metrics": args.get("metrics", []),
            "set_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        self._daily_goals.append(goal)
        
        return {"goal_set": True, "goal": goal}
    
    async def _tool_request_agent_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Request information from another agent."""
        agent_type = args.get("agent_type")
        query = args.get("query")
        
        # Broadcast request to company agents
        await self.broadcast(
            AgentMessageType.REQUEST_INFO,
            {
                "query": query,
                "requesting_agent": self.agent_id,
                "target_agent_type": agent_type
            }
        )
        
        return {"request_sent": True, "query": query}
