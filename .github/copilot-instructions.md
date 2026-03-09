# GitHub Copilot Instructions for BuizSwarm

## Repository Overview

BuizSwarm is a **Polsia-style autonomous company-building platform** that uses AI agents to create, manage, and grow businesses with minimal human intervention.

### Key Technologies
- **Backend**: Python 3.11+, FastAPI, Pydantic, SQLAlchemy
- **Frontend**: Angular 17+, TypeScript, Angular Material
- **AI/ML**: AWS Bedrock (Claude), Model Context Protocol (MCP)
- **Infrastructure**: AWS ECS, RDS Aurora, ElastiCache, Terraform
- **Task Queue**: Celery + Redis

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    BuizSwarm Platform                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  CEO Agent  │  │ Engineering │  │   Marketing Agent   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         └────────────────┼────────────────────┘              │
│              ┌───────────┴───────────┐                       │
│              │   Swarm Orchestrator   │                       │
│              └───────────┬───────────┘                       │
│  ┌───────────────────────┼───────────────────────┐           │
│  ▼                       ▼                       ▼           │
│ ┌────────────┐    ┌────────────┐    ┌────────────────────┐  │
│ │   Agent    │    │  Bedrock   │    │   MCP Client       │  │
│ │   Core     │    │  Client    │    │   (Tools/Resources)│  │
│ └────────────┘    └────────────┘    └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Coding Standards

### Python (Backend)
- Use **type hints** for all function parameters and return types
- Follow **async/await** patterns for I/O operations
- Use **Pydantic models** for all data validation
- Follow **Google Python Style Guide**
- Maximum line length: 100 characters
- Use `black` for formatting: `black . --line-length=100`
- Use `pylint` for linting

### TypeScript (Frontend)
- Follow **Angular Style Guide**
- Use **strict mode** TypeScript
- Use `gts` (Google TypeScript Style) for linting
- Prefer **standalone components**
- Use **signals** for state management
- Use **Angular Material** for UI components

### General
- Write **comprehensive docstrings** for all public APIs
- Include **error handling** with try/except blocks
- Use **structured logging** with the `logging` module
- Write **unit tests** for all new functionality

## Agent Development Guidelines

### Creating a New Agent

When adding a new agent type:

1. **Inherit from `BaseAgent`** in `backend/app/agents/base_agent.py`
2. **Define capabilities** using `AgentCapability` enum
3. **Implement required methods**:
   - `async def initialize()`: Set up agent state
   - `async def execute_task(task)`: Main task execution logic
   - `async def shutdown()`: Cleanup resources

4. **Add system prompt** in the agent's `__init__` method
5. **Register in `AgentCore`** for lifecycle management

Example:
```python
from app.agents.base_agent import BaseAgent, AgentConfig, AgentCapability

class MyNewAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.system_prompt = """You are a specialized agent that..."""
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        # Implementation here
        pass
```

### Agent Capabilities

Available capabilities:
- `STRATEGIC`: CEO-level decision making
- `CODING`: Code generation and review
- `DEPLOYMENT`: Infrastructure and deployment
- `MARKETING`: Marketing campaigns and content
- `SUPPORT`: Customer service and tickets
- `ANALYSIS`: Data analysis and reporting

## MCP (Model Context Protocol) Integration

When adding new MCP tools:

1. Define tool schema in `backend/app/core/mcp_client.py`
2. Implement tool handler function
3. Register with `MCPClient.register_tool()`
4. Add documentation in `docs/mcp-tools.md`

Example:
```python
async def my_tool_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Tool description for LLM."""
    # Implementation
    return {"result": "success"}

mcp_client.register_tool(
    name="my_tool",
    description="What this tool does",
    parameters={"param1": "string"},
    handler=my_tool_handler
)
```

## API Development

### Adding New Endpoints

1. Add route in `backend/app/api/routes.py`
2. Use Pydantic models for request/response
3. Include proper HTTP status codes
4. Add authentication/authorization
5. Document with docstrings

Example:
```python
@router.post("/companies/{company_id}/my-action")
async def my_action(
    company_id: str,
    request: MyActionRequest,
    current_user: User = Depends(get_current_user)
) -> MyActionResponse:
    """Brief description of what this endpoint does."""
    # Implementation
    pass
```

## Database Models

### Adding New Models

1. Define in `backend/app/models/`
2. Inherit from `Base` SQLAlchemy model
3. Use proper relationships with `relationship()`
4. Add migration with Alembic
5. Include indexes for frequently queried fields

Example:
```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class MyModel(Base):
    __tablename__ = "my_models"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("companies.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="my_models")
```

## Testing

### Unit Tests

- Use `pytest` for testing
- Mock external services (AWS Bedrock, Stripe, etc.)
- Use `pytest-asyncio` for async tests
- Aim for >80% code coverage

Example:
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_agent_execution():
    agent = MyAgent(config)
    with patch("app.core.bedrock_client.BedrockClient.invoke") as mock_invoke:
        mock_invoke.return_value = {"content": "test"}
        result = await agent.execute_task(task)
        assert result["status"] == "success"
```

## Environment Variables

Required environment variables:
```bash
# Application
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Stripe
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PLATFORM_FEE_PERCENT=20.0

# APIs
GITHUB_TOKEN=ghp_...
SENDGRID_API_KEY=SG.xxx
```

## Common Tasks

### Running Locally
```bash
cd backend
docker-compose up -d
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Running Tests
```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend Development
```bash
cd frontend
npm install
ng serve
# App at http://localhost:4200
```

## Deployment

### AWS Deployment
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

### Docker Build
```bash
cd backend
docker build -t buizswarm-backend .
docker run -p 8000:8000 buizswarm-backend
```

## Security Best Practices

- Never commit secrets to git
- Use AWS Secrets Manager for production credentials
- Validate all user inputs with Pydantic
- Use parameterized queries (SQLAlchemy ORM)
- Implement rate limiting on API endpoints
- Use HTTPS in production
- Regularly update dependencies

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for structural changes
- Add docstrings to all public APIs
- Include examples in documentation
- Keep API documentation in sync with code

## Pull Request Guidelines

1. **Title**: Clear, descriptive title
2. **Description**: What changed and why
3. **Tests**: Include tests for new functionality
4. **Documentation**: Update relevant docs
5. **Review**: Request review from maintainers

## Questions?

- Check existing issues: https://github.com/groupthinking/buiz-swarm/issues
- Review documentation: https://docs.buizswarm.com
- Contact: support@buizswarm.com
