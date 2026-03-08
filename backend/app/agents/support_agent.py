"""
Support Agent - Customer service, email management, and issue resolution.

The Support Agent is responsible for:
- Customer service interactions
- Email management and responses
- Support ticket handling
- FAQ and knowledge base management
- Customer satisfaction monitoring
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentConfig, TaskContext
from ..core.agent_core import AgentCapability, AgentMessage, AgentMessageType
from ..core.bedrock_client import BedrockTool
from ..core.swarm_orchestrator import TaskType

logger = logging.getLogger(__name__)


# System prompt for Support Agent
SUPPORT_SYSTEM_PROMPT = """You are the Support Agent of an autonomous AI company. Your role is to:

1. PROVIDE excellent customer service
2. MANAGE and respond to customer emails
3. HANDLE support tickets efficiently
4. MAINTAIN and improve the knowledge base
5. MONITOR customer satisfaction

Guidelines:
- Always be polite, professional, and empathetic
- Respond promptly to all customer inquiries
- Solve problems completely on the first contact when possible
- Escalate complex issues to appropriate teams
- Document all interactions thoroughly
- Follow up to ensure customer satisfaction

When responding to customers:
- Acknowledge their issue clearly
- Provide specific, actionable solutions
- Set clear expectations for resolution
- Use positive, solution-oriented language
- Personalize responses when possible

For ticket management:
- Prioritize based on severity and impact
- Keep customers informed of progress
- Meet or exceed SLA targets
- Identify patterns and root causes
"""


def get_default_support_config() -> AgentConfig:
    """Get default configuration for Support Agent."""
    return AgentConfig(
        agent_type="support",
        capabilities=[
            AgentCapability.SUPPORT,
            AgentCapability.ANALYSIS,
            AgentCapability.COMMUNICATION
        ],
        system_prompt=SUPPORT_SYSTEM_PROMPT,
        max_tokens=4096,
        temperature=0.5,  # Balanced for consistency and empathy
        enable_mcp_tools=True,
        enable_conversation_memory=True,
        auto_execute_tools=True
    )


class SupportAgent(BaseAgent):
    """
    Support Agent for customer service and issue resolution.
    
    Handles all customer-facing support activities including email responses,
    ticket management, and knowledge base maintenance.
    """
    
    def __init__(
        self,
        agent_id: str,
        company_id: str,
        config: Optional[AgentConfig] = None
    ):
        if config is None:
            config = get_default_support_config()
        
        super().__init__(agent_id, company_id, config)
        
        # Track tickets and interactions
        self._tickets: List[Dict[str, Any]] = []
        self._knowledge_base: Dict[str, Any] = {
            "faqs": [],
            "articles": [],
            "templates": {}
        }
        self._customer_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def _register_tools(self) -> None:
        """Register support-specific tools."""
        # Tool: Respond to customer email
        self.register_tool(BedrockTool(
            name="respond_to_email",
            description="Generate a response to a customer email",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_email": {
                        "type": "string",
                        "description": "Customer's email content"
                    },
                    "customer_info": {
                        "type": "object",
                        "description": "Customer information"
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["empathetic", "professional", "urgent"],
                        "description": "Response tone"
                    },
                    "include_solution": {
                        "type": "boolean",
                        "description": "Whether to include solution steps"
                    }
                },
                "required": ["customer_email"]
            },
            handler=self._tool_respond_to_email
        ))
        
        # Tool: Create support ticket
        self.register_tool(BedrockTool(
            name="create_ticket",
            description="Create a new support ticket",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID"
                    },
                    "issue": {
                        "type": "string",
                        "description": "Issue description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Ticket priority"
                    },
                    "category": {
                        "type": "string",
                        "description": "Issue category"
                    }
                },
                "required": ["customer_id", "issue"]
            },
            handler=self._tool_create_ticket
        ))
        
        # Tool: Resolve ticket
        self.register_tool(BedrockTool(
            name="resolve_ticket",
            description="Resolve a support ticket",
            input_schema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID"
                    },
                    "resolution": {
                        "type": "string",
                        "description": "Resolution description"
                    },
                    "notify_customer": {
                        "type": "boolean",
                        "description": "Whether to notify customer"
                    }
                },
                "required": ["ticket_id", "resolution"]
            },
            handler=self._tool_resolve_ticket
        ))
        
        # Tool: Search knowledge base
        self.register_tool(BedrockTool(
            name="search_knowledge_base",
            description="Search the knowledge base for information",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter"
                    }
                },
                "required": ["query"]
            },
            handler=self._tool_search_knowledge_base
        ))
        
        # Tool: Add to knowledge base
        self.register_tool(BedrockTool(
            name="add_to_knowledge_base",
            description="Add an article or FAQ to the knowledge base",
            input_schema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["faq", "article"],
                        "description": "Content type"
                    },
                    "title": {
                        "type": "string",
                        "description": "Content title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content body"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Content tags"
                    }
                },
                "required": ["type", "title", "content"]
            },
            handler=self._tool_add_to_knowledge_base
        ))
    
    async def respond_to_email(
        self,
        customer_email: str,
        customer_info: Optional[Dict[str, Any]] = None,
        tone: str = "empathetic",
        include_solution: bool = True
    ) -> Dict[str, Any]:
        """Generate a response to a customer email."""
        # Get customer history if available
        customer_id = customer_info.get("id") if customer_info else None
        history = self._customer_history.get(customer_id, []) if customer_id else []
        
        history_str = ""
        if history:
            history_str = "\nPrevious interactions:\n"
            for h in history[-3:]:  # Last 3 interactions
                history_str += f"- {h.get('date')}: {h.get('summary')}\n"
        
        prompt = f"""Generate a response to this customer email:

Customer Email:
```
{customer_email}
```

Customer Info: {json.dumps(customer_info, indent=2) if customer_info else 'Not provided'}
{history_str}

Tone: {tone}
Include Solution: {include_solution}

Provide response in JSON format:
{{
    "subject": "email subject line",
    "body": "full email body",
    "action_items": ["action1", "action2"],
    "escalate": true/false,
    "escalation_reason": "reason if escalating"
}}
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                email_response = json.loads(response[json_start:json_end])
                
                # Store in customer history
                if customer_id:
                    if customer_id not in self._customer_history:
                        self._customer_history[customer_id] = []
                    
                    self._customer_history[customer_id].append({
                        "date": datetime.utcnow().isoformat(),
                        "type": "email_response",
                        "summary": email_response.get("subject", "Response sent")
                    })
                
                return email_response
        except json.JSONDecodeError:
            pass
        
        return {
            "subject": "Re: Your Inquiry",
            "body": response,
            "action_items": [],
            "escalate": False,
            "escalation_reason": None
        }
    
    async def create_ticket(
        self,
        customer_id: str,
        issue: str,
        priority: str = "medium",
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a support ticket."""
        ticket = {
            "id": f"TICKET-{len(self._tickets) + 1000}",
            "customer_id": customer_id,
            "issue": issue,
            "priority": priority,
            "category": category or "general",
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "assigned_to": None,
            "resolution": None,
            "notes": []
        }
        
        self._tickets.append(ticket)
        
        logger.info(f"Created ticket {ticket['id']} for customer {customer_id}")
        
        return ticket
    
    async def resolve_ticket(
        self,
        ticket_id: str,
        resolution: str,
        notify_customer: bool = True
    ) -> Dict[str, Any]:
        """Resolve a support ticket."""
        ticket = None
        for t in self._tickets:
            if t.get("id") == ticket_id:
                ticket = t
                break
        
        if not ticket:
            return {"error": "Ticket not found"}
        
        ticket["status"] = "resolved"
        ticket["resolution"] = resolution
        ticket["updated_at"] = datetime.utcnow().isoformat()
        ticket["resolved_at"] = datetime.utcnow().isoformat()
        
        # Notify customer if requested
        if notify_customer:
            # This would integrate with email service
            pass
        
        return ticket
    
    async def search_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search the knowledge base."""
        results = {
            "faqs": [],
            "articles": []
        }
        
        query_lower = query.lower()
        
        # Search FAQs
        for faq in self._knowledge_base.get("faqs", []):
            if (query_lower in faq.get("question", "").lower() or
                query_lower in faq.get("answer", "").lower()):
                if not category or faq.get("category") == category:
                    results["faqs"].append(faq)
        
        # Search articles
        for article in self._knowledge_base.get("articles", []):
            if (query_lower in article.get("title", "").lower() or
                query_lower in article.get("content", "").lower()):
                if not category or article.get("category") == category:
                    results["articles"].append(article)
        
        return results
    
    async def add_to_knowledge_base(
        self,
        content_type: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add content to the knowledge base."""
        item = {
            "id": f"{content_type}_{len(self._knowledge_base.get(content_type + 's', []))}",
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if content_type == "faq":
            self._knowledge_base["faqs"].append(item)
        elif content_type == "article":
            self._knowledge_base["articles"].append(item)
        
        return item
    
    async def get_support_metrics(self) -> Dict[str, Any]:
        """Get support team metrics."""
        total_tickets = len(self._tickets)
        open_tickets = len([t for t in self._tickets if t.get("status") == "open"])
        resolved_tickets = len([t for t in self._tickets if t.get("status") == "resolved"])
        
        # Calculate average resolution time
        resolution_times = []
        for t in self._tickets:
            if t.get("status") == "resolved" and t.get("resolved_at") and t.get("created_at"):
                try:
                    created = datetime.fromisoformat(t["created_at"])
                    resolved = datetime.fromisoformat(t["resolved_at"])
                    resolution_times.append((resolved - created).total_seconds() / 3600)
                except:
                    pass
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "avg_resolution_hours": round(avg_resolution_time, 2),
            "resolution_rate": round(resolved_tickets / total_tickets * 100, 2) if total_tickets > 0 else 0
        }
    
    async def execute_task(self, task_context: TaskContext) -> Dict[str, Any]:
        """Execute a support task."""
        task_type = task_context.task_type
        params = task_context.parameters
        
        if task_type == TaskType.CUSTOMER_SUPPORT.value:
            return await self.respond_to_email(
                customer_email=params.get("customer_email", ""),
                customer_info=params.get("customer_info"),
                tone=params.get("tone", "empathetic"),
                include_solution=params.get("include_solution", True)
            )
        
        elif task_type == "create_ticket":
            return await self.create_ticket(
                customer_id=params.get("customer_id", ""),
                issue=params.get("issue", ""),
                priority=params.get("priority", "medium"),
                category=params.get("category")
            )
        
        elif task_type == "resolve_ticket":
            return await self.resolve_ticket(
                ticket_id=params.get("ticket_id", ""),
                resolution=params.get("resolution", ""),
                notify_customer=params.get("notify_customer", True)
            )
        
        elif task_type == "search_knowledge_base":
            return await self.search_knowledge_base(
                query=params.get("query", ""),
                category=params.get("category")
            )
        
        elif task_type == "get_metrics":
            return await self.get_support_metrics()
        
        else:
            return await super().execute_task(task_context)
    
    # Tool handlers
    async def _tool_respond_to_email(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Respond to email."""
        return await self.respond_to_email(
            customer_email=args.get("customer_email", ""),
            customer_info=args.get("customer_info"),
            tone=args.get("tone", "empathetic"),
            include_solution=args.get("include_solution", True)
        )
    
    async def _tool_create_ticket(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Create ticket."""
        return await self.create_ticket(
            customer_id=args.get("customer_id", ""),
            issue=args.get("issue", ""),
            priority=args.get("priority", "medium"),
            category=args.get("category")
        )
    
    async def _tool_resolve_ticket(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Resolve ticket."""
        return await self.resolve_ticket(
            ticket_id=args.get("ticket_id", ""),
            resolution=args.get("resolution", ""),
            notify_customer=args.get("notify_customer", True)
        )
    
    async def _tool_search_knowledge_base(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Search knowledge base."""
        return await self.search_knowledge_base(
            query=args.get("query", ""),
            category=args.get("category")
        )
    
    async def _tool_add_to_knowledge_base(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Add to knowledge base."""
        return await self.add_to_knowledge_base(
            content_type=args.get("type", "article"),
            title=args.get("title", ""),
            content=args.get("content", ""),
            tags=args.get("tags", [])
        )
