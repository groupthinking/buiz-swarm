"""
Marketing Agent - Ad campaigns, content creation, and outreach.

The Marketing Agent is responsible for:
- Meta Ads API integration
- Cold email campaigns
- Content generation (blog, social media)
- Social media management
- Lead generation and nurturing
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentConfig, TaskContext
from ..core.agent_core import AgentCapability
from ..core.bedrock_client import BedrockTool
from ..core.swarm_orchestrator import TaskType

logger = logging.getLogger(__name__)


# System prompt for Marketing Agent
MARKETING_SYSTEM_PROMPT = """You are the Marketing Agent of an autonomous AI company. Your role is to:

1. CREATE compelling marketing content
2. MANAGE advertising campaigns (Meta Ads, Google Ads)
3. EXECUTE cold email outreach campaigns
4. MANAGE social media presence
5. GENERATE leads and nurture prospects

Guidelines:
- Always focus on ROI and conversion optimization
- Create content that resonates with the target audience
- A/B test everything when possible
- Track and analyze campaign performance
- Maintain brand consistency across all channels
- Follow marketing best practices and compliance (CAN-SPAM, GDPR)

When creating content:
- Use persuasive copywriting techniques
- Include clear calls-to-action
- Optimize for the target platform
- Consider SEO for written content
- Make content shareable and engaging

For campaigns:
- Set clear objectives and KPIs
- Define target audiences precisely
- Allocate budget effectively
- Monitor performance daily
- Optimize based on data
"""


def get_default_marketing_config() -> AgentConfig:
    """Get default configuration for Marketing Agent."""
    return AgentConfig(
        agent_type="marketing",
        capabilities=[
            AgentCapability.MARKETING,
            AgentCapability.ANALYSIS,
            AgentCapability.CONTENT_CREATION
        ],
        system_prompt=MARKETING_SYSTEM_PROMPT,
        max_tokens=4096,
        temperature=0.8,  # Higher temperature for creative content
        enable_mcp_tools=True,
        enable_conversation_memory=True,
        auto_execute_tools=True
    )


class MarketingAgent(BaseAgent):
    """
    Marketing Agent for campaigns, content, and outreach.
    
    Handles all marketing activities including advertising, content creation,
    email campaigns, and social media management.
    """
    
    def __init__(
        self,
        agent_id: str,
        company_id: str,
        config: Optional[AgentConfig] = None
    ):
        if config is None:
            config = get_default_marketing_config()
        
        super().__init__(agent_id, company_id, config)
        
        # Track campaigns and content
        self._campaigns: List[Dict[str, Any]] = []
        self._content_pieces: List[Dict[str, Any]] = []
        self._email_sequences: List[Dict[str, Any]] = []
    
    async def _register_tools(self) -> None:
        """Register marketing-specific tools."""
        # Tool: Create ad campaign
        self.register_tool(BedrockTool(
            name="create_ad_campaign",
            description="Create an advertising campaign",
            input_schema={
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "enum": ["meta", "google", "linkedin", "twitter"],
                        "description": "Advertising platform"
                    },
                    "objective": {
                        "type": "string",
                        "enum": ["awareness", "consideration", "conversions"],
                        "description": "Campaign objective"
                    },
                    "budget": {
                        "type": "number",
                        "description": "Daily budget in USD"
                    },
                    "target_audience": {
                        "type": "object",
                        "description": "Target audience definition"
                    },
                    "creative": {
                        "type": "object",
                        "description": "Ad creative (headline, body, image, CTA)"
                    }
                },
                "required": ["platform", "objective", "budget"]
            },
            handler=self._tool_create_ad_campaign
        ))
        
        # Tool: Generate content
        self.register_tool(BedrockTool(
            name="generate_content",
            description="Generate marketing content",
            input_schema={
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "enum": ["blog_post", "social_post", "email", "ad_copy", "landing_page"],
                        "description": "Type of content"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Content topic"
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["professional", "casual", "enthusiastic", "urgent"],
                        "description": "Content tone"
                    },
                    "target_audience": {
                        "type": "string",
                        "description": "Target audience description"
                    },
                    "length": {
                        "type": "string",
                        "enum": ["short", "medium", "long"],
                        "description": "Content length"
                    }
                },
                "required": ["content_type", "topic"]
            },
            handler=self._tool_generate_content
        ))
        
        # Tool: Create email sequence
        self.register_tool(BedrockTool(
            name="create_email_sequence",
            description="Create a cold email outreach sequence",
            input_schema={
                "type": "object",
                "properties": {
                    "prospect_type": {
                        "type": "string",
                        "description": "Type of prospect"
                    },
                    "sequence_length": {
                        "type": "integer",
                        "description": "Number of emails in sequence"
                    },
                    "value_proposition": {
                        "type": "string",
                        "description": "Main value proposition"
                    },
                    "personalization": {
                        "type": "boolean",
                        "description": "Whether to include personalization"
                    }
                },
                "required": ["prospect_type", "value_proposition"]
            },
            handler=self._tool_create_email_sequence
        ))
        
        # Tool: Analyze campaign performance
        self.register_tool(BedrockTool(
            name="analyze_campaign",
            description="Analyze campaign performance",
            input_schema={
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign ID"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to analyze"
                    }
                },
                "required": ["campaign_id"]
            },
            handler=self._tool_analyze_campaign
        ))
        
        # Tool: Schedule social media posts
        self.register_tool(BedrockTool(
            name="schedule_social_posts",
            description="Schedule social media posts",
            input_schema={
                "type": "object",
                "properties": {
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Platforms to post on"
                    },
                    "posts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "scheduled_time": {"type": "string"}
                            }
                        },
                        "description": "Posts to schedule"
                    }
                },
                "required": ["platforms", "posts"]
            },
            handler=self._tool_schedule_social_posts
        ))
    
    async def generate_content(
        self,
        content_type: str,
        topic: str,
        tone: str = "professional",
        target_audience: Optional[str] = None,
        length: str = "medium"
    ) -> Dict[str, Any]:
        """Generate marketing content."""
        length_words = {
            "short": "100-200 words",
            "medium": "300-500 words",
            "long": "800-1200 words"
        }
        
        prompt = f"""Create a {content_type.replace('_', ' ')} about: {topic}

Tone: {tone}
Length: {length_words.get(length, '300-500 words')}
"""
        
        if target_audience:
            prompt += f"Target Audience: {target_audience}\n"
        
        prompt += """
Provide the content in JSON format:
{
    "title": "content title",
    "content": "the full content",
    "hashtags": ["tag1", "tag2"],
    "cta": "call to action",
    "seo_keywords": ["keyword1", "keyword2"]
}
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                content_data = json.loads(response[json_start:json_end])
                
                # Store content piece
                self._content_pieces.append({
                    "id": f"content_{len(self._content_pieces)}",
                    "type": content_type,
                    "topic": topic,
                    "created_at": datetime.utcnow().isoformat(),
                    "content": content_data
                })
                
                return content_data
        except json.JSONDecodeError:
            pass
        
        return {
            "title": topic,
            "content": response,
            "hashtags": [],
            "cta": "Learn more",
            "seo_keywords": []
        }
    
    async def create_ad_campaign(
        self,
        platform: str,
        objective: str,
        budget: float,
        target_audience: Optional[Dict[str, Any]] = None,
        creative: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an advertising campaign."""
        # Generate ad creative if not provided
        if not creative:
            creative_prompt = f"""Create ad creative for a {platform} campaign with objective: {objective}

Target Audience: {json.dumps(target_audience, indent=2) if target_audience else 'General audience'}

Provide in JSON format:
{{
    "headline": "attention-grabbing headline",
    "body": "compelling ad body text",
    "cta": "call to action button text",
    "image_description": "description of the ad image"
}}
"""
            creative_response = await self.generate_response(creative_prompt, use_memory=True)
            
            try:
                json_start = creative_response.find("{")
                json_end = creative_response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    creative = json.loads(creative_response[json_start:json_end])
            except json.JSONDecodeError:
                creative = {
                    "headline": "Discover Our Solution",
                    "body": "Transform your business with our innovative platform.",
                    "cta": "Learn More",
                    "image_description": "Professional product showcase"
                }
        
        campaign = {
            "id": f"campaign_{len(self._campaigns)}",
            "platform": platform,
            "objective": objective,
            "budget": budget,
            "target_audience": target_audience or {},
            "creative": creative,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "performance": {
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0
            }
        }
        
        self._campaigns.append(campaign)
        
        # This would integrate with actual ad platform APIs
        logger.info(f"Created {platform} campaign with ${budget}/day budget")
        
        return campaign
    
    async def create_email_sequence(
        self,
        prospect_type: str,
        value_proposition: str,
        sequence_length: int = 3,
        personalization: bool = True
    ) -> Dict[str, Any]:
        """Create a cold email outreach sequence."""
        prompt = f"""Create a {sequence_length}-email cold outreach sequence for {prospect_type} prospects.

Value Proposition: {value_proposition}
Personalization: {'Enabled' if personalization else 'Disabled'}

For each email, provide:
- Subject line
- Body text
- Call to action
- Timing (when to send)

Format as JSON:
{{
    "sequence": [
        {{
            "step": 1,
            "subject": "email subject",
            "body": "email body",
            "cta": "call to action",
            "timing": "immediate|day_1|day_3|day_7"
        }}
    ],
    "personalization_tips": ["tip1", "tip2"]
}}
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                sequence_data = json.loads(response[json_start:json_end])
                
                self._email_sequences.append({
                    "id": f"sequence_{len(self._email_sequences)}",
                    "prospect_type": prospect_type,
                    "created_at": datetime.utcnow().isoformat(),
                    "sequence": sequence_data
                })
                
                return sequence_data
        except json.JSONDecodeError:
            pass
        
        return {
            "sequence": [],
            "raw_response": response
        }
    
    async def analyze_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Analyze campaign performance."""
        campaign = None
        for c in self._campaigns:
            if c.get("id") == campaign_id:
                campaign = c
                break
        
        if not campaign:
            return {"error": "Campaign not found"}
        
        performance = campaign.get("performance", {})
        
        # Calculate metrics
        impressions = performance.get("impressions", 0)
        clicks = performance.get("clicks", 0)
        conversions = performance.get("conversions", 0)
        spend = performance.get("spend", 0)
        
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cpc = (spend / clicks) if clicks > 0 else 0
        cvr = (conversions / clicks * 100) if clicks > 0 else 0
        cpa = (spend / conversions) if conversions > 0 else 0
        
        analysis = {
            "campaign_id": campaign_id,
            "platform": campaign.get("platform"),
            "metrics": {
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "spend": spend,
                "ctr": round(ctr, 2),
                "cpc": round(cpc, 2),
                "cvr": round(cvr, 2),
                "cpa": round(cpa, 2)
            },
            "recommendations": []
        }
        
        # Generate recommendations
        if ctr < 1:
            analysis["recommendations"].append("CTR is low. Consider testing new ad creative.")
        if cvr < 2:
            analysis["recommendations"].append("Conversion rate is low. Review landing page experience.")
        if cpa > 100:
            analysis["recommendations"].append("CPA is high. Consider refining target audience.")
        
        return analysis
    
    async def execute_task(self, task_context: TaskContext) -> Dict[str, Any]:
        """Execute a marketing task."""
        task_type = task_context.task_type
        params = task_context.parameters
        
        if task_type == TaskType.MARKETING_CAMPAIGN.value:
            return await self.create_ad_campaign(
                platform=params.get("platform", "meta"),
                objective=params.get("objective", "conversions"),
                budget=params.get("budget", 50),
                target_audience=params.get("target_audience"),
                creative=params.get("creative")
            )
        
        elif task_type == TaskType.CONTENT_CREATION.value:
            return await self.generate_content(
                content_type=params.get("content_type", "blog_post"),
                topic=params.get("topic", ""),
                tone=params.get("tone", "professional"),
                target_audience=params.get("target_audience"),
                length=params.get("length", "medium")
            )
        
        elif task_type == "email_campaign":
            return await self.create_email_sequence(
                prospect_type=params.get("prospect_type", "general"),
                value_proposition=params.get("value_proposition", ""),
                sequence_length=params.get("sequence_length", 3),
                personalization=params.get("personalization", True)
            )
        
        elif task_type == "analyze_campaign":
            return await self.analyze_campaign(params.get("campaign_id", ""))
        
        else:
            return await super().execute_task(task_context)
    
    # Tool handlers
    async def _tool_create_ad_campaign(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Create ad campaign."""
        return await self.create_ad_campaign(
            platform=args.get("platform", "meta"),
            objective=args.get("objective", "conversions"),
            budget=args.get("budget", 50),
            target_audience=args.get("target_audience"),
            creative=args.get("creative")
        )
    
    async def _tool_generate_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Generate content."""
        return await self.generate_content(
            content_type=args.get("content_type", "blog_post"),
            topic=args.get("topic", ""),
            tone=args.get("tone", "professional"),
            target_audience=args.get("target_audience"),
            length=args.get("length", "medium")
        )
    
    async def _tool_create_email_sequence(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Create email sequence."""
        return await self.create_email_sequence(
            prospect_type=args.get("prospect_type", "general"),
            value_proposition=args.get("value_proposition", ""),
            sequence_length=args.get("sequence_length", 3),
            personalization=args.get("personalization", True)
        )
    
    async def _tool_analyze_campaign(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Analyze campaign."""
        return await self.analyze_campaign(args.get("campaign_id", ""))
    
    async def _tool_schedule_social_posts(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Schedule social posts."""
        # This would integrate with social media APIs
        return {
            "success": True,
            "platforms": args.get("platforms", []),
            "posts_scheduled": len(args.get("posts", [])),
            "scheduled_at": datetime.utcnow().isoformat()
        }
