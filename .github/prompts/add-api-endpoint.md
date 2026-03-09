# Add API Endpoint

Add a new REST API endpoint to the BuizSwarm backend.

## Context

FastAPI backend with the following structure:
- Routes in `backend/app/api/routes.py`
- Pydantic models for request/response validation
- SQLAlchemy for database operations
- JWT authentication with OAuth2

## Task

Add a new API endpoint for `{endpoint_path}`.

## Requirements

1. Add route in `backend/app/api/routes.py`
2. Create Pydantic request/response models
3. Implement business logic in appropriate service
4. Add authentication/authorization
5. Include proper error handling
6. Add comprehensive docstrings
7. Write unit tests

## Endpoint Details

- **Method**: {http_method}
- **Path**: `{endpoint_path}`
- **Description**: {endpoint_description}
- **Authentication**: {authentication_required}
- **Request Body**: {request_body_schema}
- **Response**: {response_schema}

## Example Implementation

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from ..services.{service_name} import {ServiceClass}
from ..models.user import User
from ..core.auth import get_current_user
from ..core.logging import logger

router = APIRouter()


class {RequestModelName}(BaseModel):
    """Request model for {endpoint_name}."""
    field1: str = Field(..., description="Description")
    field2: Optional[int] = Field(None, description="Optional field")
    
    class Config:
        json_schema_extra = {
            "example": {
                "field1": "example value",
                "field2": 42
            }
        }


class {ResponseModelName}(BaseModel):
    """Response model for {endpoint_name}."""
    id: str
    field1: str
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.{http_method}("{endpoint_path}", response_model={ResponseModelName})
async def {function_name}(
    request: {RequestModelName},
    current_user: User = Depends(get_current_user),
    service: {ServiceClass} = Depends()
) -> {ResponseModelName}:
    """
    {endpoint_description}
    
    Args:
        request: Request body containing {request_description}
        current_user: Authenticated user making the request
        service: Service dependency for business logic
        
    Returns:
        {ResponseModelName} with {response_description}
        
    Raises:
        HTTPException: If {error_conditions}
    """
    try:
        logger.info(f"{function_name} called by user {current_user.id}")
        
        result = await service.{service_method}(request, current_user)
        
        return {ResponseModelName}(**result)
        
    except ValueError as e:
        logger.warning(f"Validation error in {function_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in {function_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

## Testing

Create test file `backend/tests/api/test_{endpoint_name}.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_{function_name}_success(client: TestClient, auth_headers):
    """Test successful {endpoint_name}."""
    request_data = {
        "field1": "test",
        "field2": 42
    }
    
    with patch("app.services.{service_name}.{ServiceClass}") as mock_service:
        mock_instance = AsyncMock()
        mock_instance.{service_method}.return_value = {
            "id": "test-id",
            "field1": "test",
            "created_at": datetime.utcnow()
        }
        mock_service.return_value = mock_instance
        
        response = client.{http_method}(
            "{endpoint_path}",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["field1"] == "test"

@pytest.mark.asyncio
async def test_{function_name}_unauthorized(client: TestClient):
    """Test {endpoint_name} without authentication."""
    response = client.{http_method}("{endpoint_path}", json={})
    assert response.status_code == 401
```

## Checklist

- [ ] Route added to `backend/app/api/routes.py`
- [ ] Pydantic models created with validation
- [ ] Service method implemented
- [ ] Authentication/authorization added
- [ ] Error handling with appropriate HTTP status codes
- [ ] Comprehensive docstrings added
- [ ] Unit tests written
- [ ] API documentation updated
- [ ] Postman/curl example provided
