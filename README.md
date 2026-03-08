# BuizSwarm - Autonomous Company Building Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393.svg)](https://fastapi.tiangolo.com)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

BuizSwarm is a **Polsia-style autonomous company-building platform** that enables AI agents to create, manage, and grow businesses with minimal human intervention.

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
docker-compose up -d
```

This starts:
- FastAPI application on http://localhost:8000
- PostgreSQL database
- Redis cache
- Celery worker (background tasks)

### 4. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Dashboard**: http://localhost:4200 (after starting frontend)

## 📚 API Documentation

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

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

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
