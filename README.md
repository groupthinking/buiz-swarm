# BuizSwarm - Autonomous Company Building Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393.svg)](https://fastapi.tiangolo.com)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

BuizSwarm is a **Polsia-style autonomous company-building platform** that enables AI agents to create, manage, and grow businesses with minimal human intervention.

Canonical platform domain: `agentbroker.app`. The operator dashboard lives at `app.agentbroker.app`, and tenant businesses are intended to live under `*.agentbroker.app` with optional custom domains later.

OpenClaw integration: the backend can register an `openclaw` MCP server preset that talks to an HTTP bridge, and the bridge uses the OpenClaw gateway WebSocket with shared-secret auth from `OPENCLAW_GATEWAY_TOKEN` or the mounted `~/.openclaw/openclaw.json`.

ProfitMax profile: the vendored ProfitMax workspace now exposes a workflow library on top of the imported role packs. The first revenue workflows are `lead_qualification`, `outbound_personalization`, and `offer_pricing_review`, and each workflow carries a curated operator-skill stack for research, pricing, handoff, and execution.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [GitHub Copilot](#-github-copilot)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Features

### Autonomous Operations
- **Daily AI Cycles**: CEO agents automatically evaluate business state and make strategic decisions
- **Multi-Agent Swarm**: Coordinated teams of specialized agents (CEO, Engineering, Marketing, Support)
- **Infrastructure Provisioning**: Automatic setup of servers, databases, email, and payment processing
- **Revenue Sharing**: 20% platform fee model with automatic payout distribution

### Agent Capabilities
| Agent | Capabilities |
|-------|-------------|
| **CEO** | Strategic planning, decision making, task prioritization, business analysis |
| **Engineering** | Code generation, deployment, bug fixes, infrastructure management |
| **Marketing** | Ad campaigns, content creation, cold email outreach, social media |
| **Support** | Customer service, ticket management, knowledge base maintenance |

### Platform Features
- **Multi-Tenant Architecture**: Support for 1000+ concurrent companies
- **Real-Time Dashboard**: Monitor all agent activities and company metrics
- **MCP Integration**: Connect to external tools via Model Context Protocol
- **AWS Bedrock**: Powered by Claude for intelligent agent responses

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        BuizSwarm Platform                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  CEO Agent  │  │ Engineering │  │   Marketing Agent   │  │
│  │             │  │    Agent    │  │                     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                    │              │
│         └────────────────┼────────────────────┘              │
│                          │                                   │
│              ┌───────────┴───────────┐                       │
│              │   Swarm Orchestrator   │                       │
│              │  (Task Queue & Coord)  │                       │
│              └───────────┬───────────┘                       │
│                          │                                   │
│  ┌───────────────────────┼───────────────────────┐           │
│  │                       │                       │           │
│  ▼                       ▼                       ▼           │
│ ┌────────────┐    ┌────────────┐    ┌────────────────────┐  │
│ │   Agent    │    │  Bedrock   │    │   MCP Client       │  │
│ │   Core     │    │  Client    │    │   (Tools/Resources)│  │
│ └────────────┘    └────────────┘    └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐         ┌──────────┐         ┌──────────┐
   │  AWS    │         │  Stripe  │         │  GitHub  │
   │Bedrock  │         │ Connect  │         │   API    │
   └─────────┘         └──────────┘         └──────────┘
```

## 📁 Project Structure

```
buiz-swarm/
├── backend/
│   ├── app/
│   │   ├── core/               # Core platform modules
│   │   │   ├── agent_core.py       # Agent lifecycle management
│   │   │   ├── swarm_orchestrator.py # Multi-agent coordination
│   │   │   ├── bedrock_client.py   # AWS Bedrock integration
│   │   │   └── mcp_client.py       # MCP protocol implementation
│   │   ├── agents/             # Agent implementations
│   │   │   ├── base_agent.py       # Base agent class
│   │   │   ├── ceo_agent.py        # Strategic decision maker
│   │   │   ├── engineering_agent.py # Code/build/deploy
│   │   │   ├── marketing_agent.py  # Ads, content, outreach
│   │   │   └── support_agent.py    # Customer service
│   │   ├── models/             # Data models
│   │   ├── services/           # Business services
│   │   ├── api/                # API routes
│   │   ├── config.py           # Configuration
│   │   └── main.py             # FastAPI entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/                   # Angular dashboard
├── infrastructure/             # Terraform AWS infrastructure
└── README.md
```

## 🤖 GitHub Copilot

This repository is configured for **GitHub Copilot** with custom instructions and reusable prompts for common development tasks.

### Copilot Instructions

Copilot configuration is in `.github/copilot-instructions.md` which includes:
- Repository overview and architecture
- Coding standards (Python & TypeScript)
- Agent development guidelines
- MCP tool integration patterns
- API development best practices
- Database model conventions
- Testing requirements

### Reusable Prompts

Pre-built prompts in `.github/prompts/` for common tasks:

| Prompt | Use Case |
|--------|----------|
| `create-agent.md` | Create a new agent type |
| `add-api-endpoint.md` | Add REST API endpoint |
| `add-mcp-tool.md` | Add MCP tool for agents |
| `fix-bug.md` | Fix bugs with regression tests |

### Using Copilot

1. Install GitHub Copilot extension in your IDE
2. Review `.github/copilot-instructions.md` for project context
3. Use prompts from `.github/prompts/` for guided development
4. Follow coding standards outlined in instructions

### Example: Creating a New Agent

```markdown
@copilot Using .github/prompts/create-agent.md, create a new DataAnalysisAgent that can analyze company metrics and generate reports.
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- AWS Account with Bedrock access
- Stripe Account (for payments)

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/buiz-swarm.git
cd buiz-swarm/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` file:

```bash
# Application
DEBUG=true
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/buizswarm
REDIS_URL=redis://localhost:6379/0

# AWS Bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PLATFORM_FEE_PERCENT=20.0

# External APIs
GITHUB_TOKEN=ghp_...
SENDGRID_API_KEY=SG.xxx
```

### 3. Run with Docker Compose

```bash
docker compose -f backend/docker-compose.yml -f backend/docker-compose.openclaw.yml up -d
```

This starts:
- FastAPI application on http://localhost:8010
- OpenClaw bridge on http://localhost:3016
- PostgreSQL database
- Redis cache
- Celery worker (background tasks)

### 4. Access the Application

- **API Documentation**: http://localhost:8010/docs
- **Health Check**: http://localhost:8010/health
- **OpenClaw Bridge Health**: http://localhost:3016/health
- **Dashboard**: http://localhost:4200 (after starting frontend)

## Domain Strategy

The first real platform domain is `agentbroker.app`.

- Operator dashboard: `app.agentbroker.app`
- Tenant businesses: `*.agentbroker.app`
- Optional customer-owned domains: supported later via the stored `custom_domain` field

Recommended Vercel setup:
- Put the dashboard/frontend on the operator domain `app.agentbroker.app`
- Route tenant businesses on a wildcard under `*.agentbroker.app`
- Keep the backend/API on its own service and proxy `/api/*` from the dashboard domain in production
- Use Vercel-managed nameservers when you want wildcard SSL and domain management in one place

The business-creation flow now defaults to this domain model automatically.

## OpenClaw Integration

BuizSwarm should stay in `/Users/garvey/Dev/buiz-swarm`. Do not move the source into `~/.openclaw`.

Use the Docker override at `backend/docker-compose.openclaw.yml` to mount the host OpenClaw runtime into the `api` and `worker` containers and point them at the host gateway:

```bash
cd backend
docker compose -f docker-compose.yml -f docker-compose.openclaw.yml up -d
# includes api, worker, db, redis, flower, and openclaw-bridge
```

The override expects these defaults:

- `OPENCLAW_HOST_DIR=/Users/garvey/.openclaw`
- `OPENCLAW_HOME=/openclaw` inside the containers
- `OPENCLAW_GATEWAY_URL=http://host.docker.internal:18789`
- `OPENCLAW_BRIDGE_URL=http://openclaw-bridge:3006`

This keeps OpenClaw as the host-level runtime and lets BuizSwarm consume it without mixing source code into the runtime directory.

## 📚 API Documentation

### ProfitMax Workflow Library

```bash
# Inspect the active ProfitMax profile and curated operator skills
GET /api/v1/profiles/current
GET /api/v1/profiles/current/skills

# List the revenue workflows available to a company
GET /api/v1/companies/{company_id}/workflows

# Run a workflow
POST /api/v1/companies/{company_id}/workflows/lead_qualification/run
{
  "inputs": {
    "company_name": "Example Co",
    "contact_name": "Jane Doe",
    "lead_source": "telegram",
    "pain_points": ["needs pipeline growth", "no follow-up system"],
    "budget_signal": "$2k-$5k/mo",
    "timeline": "this month",
    "notes": "Warm inbound lead"
  }
}
```

### Company Management

```bash
# Create a company
POST /api/v1/companies
{
  "name": "My AI Company",
  "description": "An autonomous AI business",
  "industry": "Technology"
}

# Get company status
GET /api/v1/companies/{company_id}/status

# Trigger daily cycle
POST /api/v1/companies/{company_id}/daily-cycle

# Pause/Resume company
POST /api/v1/companies/{company_id}/pause
POST /api/v1/companies/{company_id}/resume
```

### Task Management

```bash
# Create a task
POST /api/v1/companies/{company_id}/tasks
{
  "task_type": "content_creation",
  "title": "Write blog post",
  "description": "Create a blog post about AI",
  "priority": "high"
}

# List tasks
GET /api/v1/companies/{company_id}/tasks
```

### Billing

```bash
# Record revenue
POST /api/v1/companies/{company_id}/revenue
{
  "amount": 1000.00,
  "source": "stripe_payment",
  "description": "Monthly subscription"
}

# Get billing summary
GET /api/v1/companies/{company_id}/billing
```

## 🏗️ Infrastructure Deployment

### AWS Deployment with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="db_password=your-password" -var="secret_key=your-secret"

# Apply deployment
terraform apply -var="db_password=your-password" -var="secret_key=your-secret"
```

### Deployed Resources

- **ECS Fargate**: Container orchestration with auto-scaling
- **RDS Aurora**: Serverless PostgreSQL database
- **ElastiCache Redis**: Caching and message queue
- **Application Load Balancer**: Traffic distribution
- **CloudWatch**: Logging and monitoring
- **Secrets Manager**: Secure credential storage

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `ENVIRONMENT` | Deployment environment | `production` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `BEDROCK_MODEL_ID` | Claude model ID | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `STRIPE_SECRET_KEY` | Stripe API key | - |
| `AGENT_DAILY_CYCLE_HOUR` | Hour to run daily cycles (UTC) | `9` |

### Agent Configuration

Each agent can be configured via the `AgentConfig` class:

```python
from app.agents.base_agent import AgentConfig

config = AgentConfig(
    agent_type="ceo",
    capabilities=[AgentCapability.STRATEGIC],
    system_prompt="Custom system prompt...",
    max_tokens=4096,
    temperature=0.7,
    enable_mcp_tools=True
)
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

## 📊 Monitoring

### System Health

```bash
GET /api/v1/system/health
```

### MCP Status

```bash
GET /api/v1/system/mcp-status
```

### Platform Statistics

```bash
GET /api/v1/system/stats
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development with Copilot

This repo is Copilot-enabled. Use `.github/prompts/` for guided development:
- Creating new agents
- Adding API endpoints
- Adding MCP tools
- Fixing bugs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Polsia.com** - Inspiration for autonomous company building
- **AWS Bedrock** - LLM inference platform
- **Model Context Protocol** - Tool integration standard
- **Claude** - AI model powering agent intelligence

## 📞 Support

- **Documentation**: https://docs.buizswarm.com
- **Issues**: https://github.com/yourusername/buiz-swarm/issues
- **Email**: support@buizswarm.com

---

Built with ❤️ by the BuizSwarm Team
