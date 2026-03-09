# Create New Agent

Create a new agent for the BuizSwarm platform.

## Context

This is a multi-agent autonomous company-building platform using:
- FastAPI backend with Python 3.11+
- AWS Bedrock (Claude) for LLM inference
- Agent Core for lifecycle management
- Swarm Orchestrator for coordination

## Task

Create a new agent type called `{agent_name}` that handles `{agent_capability}`.

## Requirements

1. Create file at `backend/app/agents/{agent_file_name}.py`
2. Inherit from `BaseAgent` class
3. Define appropriate capabilities
4. Implement required methods:
   - `__init__`: Set up agent configuration and system prompt
   - `initialize`: Async initialization
   - `execute_task`: Main task execution logic
   - `shutdown`: Cleanup
5. Add comprehensive docstrings
6. Include error handling
7. Add type hints throughout

## Agent Details

- **Agent Name**: {agent_name}
- **Capability**: {agent_capability}
- **Description**: {agent_description}
- **System Prompt**: {system_prompt}

## Example Structure

```python
"""
{agent_name} Agent - {agent_description}
"""
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentConfig, AgentCapability, AgentState
from ..core.bedrock_client import BedrockClient
from ..models.task import Task

logger = logging.getLogger(__name__)


class {AgentClassName}(BaseAgent):
    """
    {agent_description}
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.system_prompt = """{system_prompt}"""
        self.bedrock = BedrockClient()
    
    async def initialize(self) -> None:
        """Initialize the agent."""
        await super().initialize()
        # Add custom initialization
        logger.info(f"{agent_name} agent initialized")
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            task: The task to execute
            
        Returns:
            Task execution result
        """
        try:
            await self.transition_to(AgentState.EXECUTING)
            
            # Task execution logic here
            result = await self._process_task(task)
            
            await self.transition_to(AgentState.IDLE)
            return result
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            await self.transition_to(AgentState.ERROR)
            raise
    
    async def _process_task(self, task: Task) -> Dict[str, Any]:
        """Process the specific task."""
        # Implementation
        pass
    
    async def shutdown(self) -> None:
        """Shutdown the agent."""
        await super().shutdown()
        logger.info(f"{agent_name} agent shutdown")
```

## Additional Requirements

- [ ] Add unit tests in `backend/tests/agents/test_{agent_file_name}.py`
- [ ] Register agent in `backend/app/agents/__init__.py`
- [ ] Update agent factory if applicable
- [ ] Add documentation to README.md
- [ ] Include example usage in docstrings

## Testing

Test the agent with:
```python
pytest backend/tests/agents/test_{agent_file_name}.py -v
```
