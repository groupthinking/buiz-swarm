"""
Engineering Agent - Code generation, deployment, and infrastructure management.

The Engineering Agent is responsible for:
- Code generation and review
- GitHub integration
- Deployment automation
- Bug detection and fixing
- Infrastructure provisioning
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentConfig, TaskContext
from ..core.agent_core import AgentCapability
from ..core.bedrock_client import BedrockTool
from ..core.swarm_orchestrator import TaskType, TaskPriority

logger = logging.getLogger(__name__)


# System prompt for Engineering Agent
ENGINEERING_SYSTEM_PROMPT = """You are the Engineering Agent of an autonomous AI company. Your role is to:

1. WRITE clean, production-quality code
2. REVIEW code for quality and security
3. DEPLOY applications to production
4. FIX bugs and resolve technical issues
5. MANAGE infrastructure and DevOps

Guidelines:
- Write code that follows best practices and industry standards
- Always consider security, scalability, and maintainability
- Use appropriate design patterns and architecture
- Write comprehensive tests for all code
- Document your code thoroughly
- Follow the company's coding standards

When generating code:
- Use modern frameworks and libraries
- Implement proper error handling
- Include logging and monitoring
- Consider performance implications
- Write type hints and docstrings

For deployments:
- Use CI/CD best practices
- Implement proper rollback strategies
- Monitor deployment health
- Ensure zero-downtime deployments when possible
"""


def get_default_engineering_config() -> AgentConfig:
    """Get default configuration for Engineering Agent."""
    return AgentConfig(
        agent_type="engineering",
        capabilities=[
            AgentCapability.ENGINEERING,
            AgentCapability.INFRASTRUCTURE,
            AgentCapability.ANALYSIS
        ],
        system_prompt=ENGINEERING_SYSTEM_PROMPT,
        max_tokens=4096,
        temperature=0.3,  # Lower temperature for more deterministic code
        enable_mcp_tools=True,
        enable_conversation_memory=True,
        auto_execute_tools=True
    )


class EngineeringAgent(BaseAgent):
    """
    Engineering Agent for code and infrastructure management.
    
    Handles all technical aspects of the company including development,
    deployment, and infrastructure.
    """
    
    def __init__(
        self,
        agent_id: str,
        company_id: str,
        config: Optional[AgentConfig] = None
    ):
        if config is None:
            config = get_default_engineering_config()
        
        super().__init__(agent_id, company_id, config)
        
        # Track deployments and code changes
        self._deployments: List[Dict[str, Any]] = []
        self._code_reviews: List[Dict[str, Any]] = []
    
    async def _register_tools(self) -> None:
        """Register engineering-specific tools."""
        # Tool: Generate code
        self.register_tool(BedrockTool(
            name="generate_code",
            description="Generate code for a specific feature or function",
            input_schema={
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Programming language"
                    },
                    "feature": {
                        "type": "string",
                        "description": "Feature to implement"
                    },
                    "requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of requirements"
                    },
                    "framework": {
                        "type": "string",
                        "description": "Framework to use (optional)"
                    }
                },
                "required": ["language", "feature"]
            },
            handler=self._tool_generate_code
        ))
        
        # Tool: Review code
        self.register_tool(BedrockTool(
            name="review_code",
            description="Review code for quality, security, and best practices",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to review"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language"
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["security", "performance", "readability", "testing"]
                        },
                        "description": "Areas to focus on"
                    }
                },
                "required": ["code", "language"]
            },
            handler=self._tool_review_code
        ))
        
        # Tool: Create GitHub PR
        self.register_tool(BedrockTool(
            name="create_pull_request",
            description="Create a pull request on GitHub",
            input_schema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name"
                    },
                    "title": {
                        "type": "string",
                        "description": "PR title"
                    },
                    "description": {
                        "type": "string",
                        "description": "PR description"
                    }
                },
                "required": ["repo", "branch", "title"]
            },
            handler=self._tool_create_pull_request
        ))
        
        # Tool: Deploy application
        self.register_tool(BedrockTool(
            name="deploy_application",
            description="Deploy application to production",
            input_schema={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Application name"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["staging", "production"],
                        "description": "Deployment environment"
                    },
                    "version": {
                        "type": "string",
                        "description": "Version to deploy"
                    }
                },
                "required": ["app_name", "environment"]
            },
            handler=self._tool_deploy_application
        ))
        
        # Tool: Fix bug
        self.register_tool(BedrockTool(
            name="fix_bug",
            description="Analyze and fix a bug",
            input_schema={
                "type": "object",
                "properties": {
                    "bug_description": {
                        "type": "string",
                        "description": "Description of the bug"
                    },
                    "error_logs": {
                        "type": "string",
                        "description": "Error logs or stack traces"
                    },
                    "affected_code": {
                        "type": "string",
                        "description": "Code that may be affected"
                    }
                },
                "required": ["bug_description"]
            },
            handler=self._tool_fix_bug
        ))
    
    async def generate_code(
        self,
        language: str,
        feature: str,
        requirements: Optional[List[str]] = None,
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate code for a feature."""
        req_str = "\n".join(f"- {r}" for r in (requirements or []))
        framework_str = f" using {framework}" if framework else ""
        
        prompt = f"""Generate {language} code{framework_str} for the following feature:

Feature: {feature}

Requirements:
{req_str}

Please provide:
1. Complete, production-ready code
2. Type hints and docstrings
3. Error handling
4. Unit tests
5. Brief explanation of the implementation

Format your response as:
```json
{{
    "code": "the complete code",
    "tests": "the test code",
    "explanation": "brief explanation",
    "dependencies": ["dep1", "dep2"]
}}
```
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                code_data = json.loads(response[json_start:json_end])
                return code_data
        except json.JSONDecodeError:
            pass
        
        # Fallback: return raw response
        return {
            "code": response,
            "tests": "",
            "explanation": "See code for details",
            "dependencies": []
        }
    
    async def review_code(
        self,
        code: str,
        language: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Review code for quality and issues."""
        focus_str = ", ".join(focus_areas or ["general quality"])
        
        prompt = f"""Review the following {language} code, focusing on {focus_str}:

```{language}
{code}
```

Provide your review in JSON format:
{{
    "overall_score": 1-10,
    "issues": [
        {{
            "severity": "critical|high|medium|low",
            "category": "security|performance|readability|bug",
            "description": "issue description",
            "suggestion": "how to fix"
        }}
    ],
    "strengths": ["strength1", "strength2"],
    "recommendations": ["rec1", "rec2"]
}}
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                review = json.loads(response[json_start:json_end])
                self._code_reviews.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "review": review
                })
                return review
        except json.JSONDecodeError:
            pass
        
        return {
            "overall_score": 5,
            "issues": [],
            "strengths": ["Code provided for review"],
            "recommendations": ["Please provide structured review"],
            "raw_response": response
        }
    
    async def fix_bug(
        self,
        bug_description: str,
        error_logs: Optional[str] = None,
        affected_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze and fix a bug."""
        prompt = f"""Analyze and fix the following bug:

Bug Description:
{bug_description}

"""
        
        if error_logs:
            prompt += f"Error Logs:\n```\n{error_logs}\n```\n\n"
        
        if affected_code:
            prompt += f"Affected Code:\n```\n{affected_code}\n```\n\n"
        
        prompt += """Provide your analysis and fix in JSON format:
{
    "root_cause": "explanation of the root cause",
    "fix": "the corrected code",
    "prevention": "how to prevent similar bugs",
    "tests": "test cases to verify the fix"
}
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                fix_data = json.loads(response[json_start:json_end])
                return fix_data
        except json.JSONDecodeError:
            pass
        
        return {
            "root_cause": "Unable to parse analysis",
            "fix": response,
            "prevention": "N/A",
            "tests": ""
        }
    
    async def setup_infrastructure(
        self,
        infrastructure_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up infrastructure for the company."""
        # This would integrate with infrastructure_service
        # For now, return a plan
        
        prompt = f"""Create an infrastructure setup plan for:

Type: {infrastructure_type}
Configuration:
{json.dumps(config, indent=2)}

Provide the setup plan in JSON format with:
- Resources needed
- Configuration steps
- Security considerations
- Estimated costs
"""
        
        response = await self.generate_response(prompt, use_memory=True)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"plan": response, "parsed": False}
    
    async def execute_task(self, task_context: TaskContext) -> Dict[str, Any]:
        """Execute an engineering task."""
        task_type = task_context.task_type
        params = task_context.parameters
        
        if task_type == TaskType.CODE_GENERATION.value:
            return await self.generate_code(
                language=params.get("language", "python"),
                feature=params.get("feature", ""),
                requirements=params.get("requirements"),
                framework=params.get("framework")
            )
        
        elif task_type == TaskType.CODE_REVIEW.value:
            return await self.review_code(
                code=params.get("code", ""),
                language=params.get("language", "python"),
                focus_areas=params.get("focus_areas")
            )
        
        elif task_type == TaskType.BUG_FIX.value:
            return await self.fix_bug(
                bug_description=params.get("bug_description", ""),
                error_logs=params.get("error_logs"),
                affected_code=params.get("affected_code")
            )
        
        elif task_type == TaskType.DEPLOYMENT.value:
            # Handle deployment
            return await self._handle_deployment(params)
        
        elif task_type == TaskType.INFRASTRUCTURE_SETUP.value:
            return await self.setup_infrastructure(
                infrastructure_type=params.get("infrastructure_type", "web_server"),
                config=params.get("config", {})
            )
        
        else:
            return await super().execute_task(task_context)
    
    async def _handle_deployment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deployment task."""
        deployment = {
            "app_name": params.get("app_name"),
            "environment": params.get("environment", "staging"),
            "version": params.get("version"),
            "deployed_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        # This would integrate with actual deployment service
        # For now, simulate deployment
        deployment["status"] = "completed"
        self._deployments.append(deployment)
        
        return {
            "success": True,
            "deployment": deployment
        }
    
    # Tool handlers
    async def _tool_generate_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Generate code."""
        return await self.generate_code(
            language=args.get("language", "python"),
            feature=args.get("feature", ""),
            requirements=args.get("requirements"),
            framework=args.get("framework")
        )
    
    async def _tool_review_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Review code."""
        return await self.review_code(
            code=args.get("code", ""),
            language=args.get("language", "python"),
            focus_areas=args.get("focus_areas")
        )
    
    async def _tool_create_pull_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Create GitHub PR."""
        # This would integrate with GitHub API
        return {
            "success": True,
            "pr_url": f"https://github.com/{args.get('repo')}/pull/123",
            "branch": args.get("branch"),
            "title": args.get("title")
        }
    
    async def _tool_deploy_application(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Deploy application."""
        return await self._handle_deployment(args)
    
    async def _tool_fix_bug(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Fix bug."""
        return await self.fix_bug(
            bug_description=args.get("bug_description", ""),
            error_logs=args.get("error_logs"),
            affected_code=args.get("affected_code")
        )
