# Contributing to BuizSwarm

Thank you for your interest in contributing to BuizSwarm! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [GitHub Copilot](#github-copilot)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- AWS Account (for Bedrock access)
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/buiz-swarm.git
cd buiz-swarm
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/groupthinking/buiz-swarm.git
```

## Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
ng serve
```

### Docker Setup (Recommended)

```bash
cd backend
docker-compose up -d
```

This starts:
- FastAPI application on http://localhost:8000
- PostgreSQL database on port 5432
- Redis on port 6379
- Celery worker

## Coding Standards

### Python

- **Type hints**: All functions must have type annotations
- **Docstrings**: All public functions/classes need docstrings (Google style)
- **Async/await**: Use async patterns for I/O operations
- **Formatting**: Use `black` with 100 character line length
- **Linting**: Use `pylint` for code quality

```bash
# Format code
black . --line-length=100

# Lint code
pylint .
```

### TypeScript/Angular

- Follow Angular Style Guide
- Use strict TypeScript mode
- Use `gts` for linting and formatting
- Prefer standalone components
- Use Angular Material for UI

```bash
# Format code
npm run fix

# Lint code
npm run lint
```

### General

- Write clear, self-documenting code
- Keep functions small and focused
- Use meaningful variable names
- Add comments for complex logic
- Handle errors gracefully

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-marketing-agent`
- `bugfix/fix-task-queue`
- `docs/update-api-docs`
- `refactor/improve-bedrock-client`

### Commit Messages

Follow conventional commits:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(agents): add support for custom agent prompts

fix(swarm): resolve race condition in task queue

docs(api): add authentication examples
```

## Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_agents.py -v

# Frontend tests
cd frontend
npm test
```

### Writing Tests

- Write tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names
- Follow AAA pattern: Arrange, Act, Assert
- Mock external services (AWS, Stripe, etc.)

Example:
```python
@pytest.mark.asyncio
async def test_agent_executes_task_successfully():
    """Test that agent can execute a task and return result."""
    # Arrange
    agent = TestAgent(config)
    task = create_test_task()
    
    # Act
    result = await agent.execute_task(task)
    
    # Assert
    assert result["status"] == "success"
    assert "data" in result
```

## Pull Request Process

1. **Update your branch**:
```bash
git fetch upstream
git rebase upstream/main
```

2. **Run all tests** and ensure they pass

3. **Update documentation** if needed

4. **Create pull request** with:
   - Clear title describing the change
   - Detailed description of what changed and why
   - Reference any related issues
   - Screenshots for UI changes
   - Test results

5. **Code review**:
   - Address review comments
   - Keep discussion constructive
   - Make requested changes

6. **Merge**:
   - Squash commits if requested
   - Delete branch after merge

## GitHub Copilot

This repository is configured for GitHub Copilot. Copilot instructions are in `.github/copilot-instructions.md`.

### Using Copilot

1. **Install GitHub Copilot** extension in your IDE
2. **Review copilot-instructions.md** before starting work
3. **Use prompts** from `.github/prompts/` for common tasks:
   - `create-agent.md`: Creating new agents
   - `add-api-endpoint.md`: Adding API endpoints
   - `add-mcp-tool.md`: Adding MCP tools
   - `fix-bug.md`: Fixing bugs

### Copilot Best Practices

- Provide clear context in comments
- Use descriptive variable names
- Break complex tasks into smaller functions
- Review Copilot suggestions carefully
- Test generated code thoroughly

## Questions?

- Check existing [issues](https://github.com/groupthinking/buiz-swarm/issues)
- Review [documentation](https://docs.buizswarm.com)
- Join our [Discord](https://discord.gg/buizswarm)
- Email: support@buizswarm.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to BuizSwarm! 🚀
