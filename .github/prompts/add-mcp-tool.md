# Add MCP Tool

Add a new tool to the Model Context Protocol (MCP) for agent use.

## Context

MCP (Model Context Protocol) allows agents to interact with external systems through standardized tools. The MCP client is in `backend/app/core/mcp_client.py`.

## Task

Add a new MCP tool called `{tool_name}`.

## Requirements

1. Define tool schema in `backend/app/core/mcp_client.py`
2. Implement tool handler function
3. Register tool with MCP client
4. Add error handling
5. Write unit tests
6. Document the tool

## Tool Details

- **Tool Name**: {tool_name}
- **Description**: {tool_description}
- **Parameters**: {tool_parameters}
- **Returns**: {tool_returns}

## Example Implementation

```python
# In backend/app/core/mcp_client.py

async def {tool_name}_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    {tool_description}
    
    Args:
        {param_descriptions}
        
    Returns:
        {return_description}
        
    Raises:
        ValueError: If {validation_errors}
        Exception: If {execution_errors}
    """
    try:
        # Validate parameters
        required_params = [{required_params_list}]
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Extract parameters
        {param_extraction}
        
        # Execute tool logic
        result = await {execution_logic}
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        logger.warning(f"{tool_name} validation error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": "validation"
        }
    except Exception as e:
        logger.error(f"{tool_name} execution error: {e}")
        return {
            "status": "error",
            "error": "Internal tool error",
            "error_type": "internal"
        }

# Register in MCPClient.__init__ or a registration function
self.register_tool(
    name="{tool_name}",
    description="""{tool_description}""",
    parameters={{
        "type": "object",
        "properties": {{
            {parameter_schema}
        }},
        "required": [{required_params_list}]
    }},
    handler={tool_name}_handler
)
```

## Tool Registration

In `backend/app/core/mcp_client.py`, add to `MCPClient` class:

```python
def _register_default_tools(self) -> None:
    """Register default MCP tools."""
    # ... existing tools ...
    
    self.register_tool(
        name="{tool_name}",
        description="{tool_description}",
        parameters={{
            "type": "object",
            "properties": {{
                {parameter_schema}
            }},
            "required": [{required_params_list}]
        }},
        handler=self._{tool_name}_handler
    )

async def _{tool_name}_handler(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for {tool_name} tool."""
    return await {tool_name}_handler(params)
```

## Testing

Create test file `backend/tests/core/test_mcp_{tool_name}.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.core.mcp_client import MCPClient

@pytest.mark.asyncio
async def test_{tool_name}_success():
    """Test {tool_name} tool success case."""
    client = MCPClient()
    
    params = {{
        {test_params}
    }}
    
    result = await client.execute_tool("{tool_name}", params)
    
    assert result["status"] == "success"
    assert "data" in result

@pytest.mark.asyncio
async def test_{tool_name}_missing_params():
    """Test {tool_name} with missing parameters."""
    client = MCPClient()
    
    result = await client.execute_tool("{tool_name}", {{}})
    
    assert result["status"] == "error"
    assert "error_type" in result

@pytest.mark.asyncio
async def test_{tool_name}_execution_error():
    """Test {tool_name} execution error handling."""
    client = MCPClient()
    
    with patch("{module_path}") as mock_exec:
        mock_exec.side_effect = Exception("Test error")
        
        params = {{}}
        result = await client.execute_tool("{tool_name}", params)
        
        assert result["status"] == "error"
        assert result["error_type"] == "internal"
```

## Documentation

Add to `docs/mcp-tools.md`:

```markdown
### {tool_name}

{tool_description}

**Parameters:**
{parameter_docs}

**Returns:**
{return_docs}

**Example:**
```json
{{
  "tool": "{tool_name}",
  "params": {{
    {example_params}
  }}
}}
```

**Example Response:**
```json
{{
  "status": "success",
  "data": {{
    {example_response}
  }}
}}
```
```

## Checklist

- [ ] Tool handler implemented with error handling
- [ ] Tool registered in MCP client
- [ ] Parameter validation added
- [ ] Unit tests written
- [ ] Documentation added
- [ ] Example usage provided
- [ ] Tested with actual agent
