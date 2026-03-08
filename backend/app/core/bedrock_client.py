"""
AWS Bedrock Client - Claude integration for LLM inference.

Provides streaming responses, tool use, function calling, and conversation memory
for AI agents in the BuizSwarm platform.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime

import boto3
from botocore.config import Config as BotoConfig

from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class BedrockTool:
    """Tool definition for Claude function calling."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[Callable[[Dict[str, Any]], Any]] = None
    
    def to_claude_format(self) -> Dict[str, Any]:
        """Convert to Claude tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


@dataclass
class BedrockMessage:
    """Message in a Bedrock conversation."""
    role: str  # "user", "assistant", "system"
    content: Union[str, List[Dict[str, Any]]]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_claude_format(self) -> Dict[str, Any]:
        """Convert to Claude message format."""
        return {
            "role": self.role,
            "content": self.content
        }
    
    @classmethod
    def user(cls, content: str, **metadata) -> 'BedrockMessage':
        """Create a user message."""
        return cls(role="user", content=content, metadata=metadata)
    
    @classmethod
    def assistant(cls, content: str, **metadata) -> 'BedrockMessage':
        """Create an assistant message."""
        return cls(role="assistant", content=content, metadata=metadata)
    
    @classmethod
    def system(cls, content: str, **metadata) -> 'BedrockMessage':
        """Create a system message."""
        return cls(role="system", content=content, metadata=metadata)
    
    @classmethod
    def tool_use(cls, tool_name: str, tool_input: Dict[str, Any], tool_use_id: str) -> 'BedrockMessage':
        """Create a tool use message."""
        return cls(
            role="assistant",
            content=[{
                "type": "tool_use",
                "id": tool_use_id,
                "name": tool_name,
                "input": tool_input
            }]
        )
    
    @classmethod
    def tool_result(cls, tool_use_id: str, result: Any, is_error: bool = False) -> 'BedrockMessage':
        """Create a tool result message."""
        content = {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": str(result) if not isinstance(result, str) else result
        }
        if is_error:
            content["is_error"] = True
        
        return cls(role="user", content=[content])


@dataclass
class BedrockResponse:
    """Response from Bedrock/Claude."""
    content: str
    stop_reason: str
    usage: Dict[str, int]
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None


class ConversationMemory:
    """Manages conversation history with summarization and pruning."""
    
    def __init__(self, max_messages: int = 50, max_tokens: int = 100000):
        self.messages: List[BedrockMessage] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.summary: Optional[str] = None
        self._token_count: int = 0
    
    def add_message(self, message: BedrockMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        
        # Estimate token count (rough approximation)
        content_str = str(message.content)
        self._token_count += len(content_str) // 4
        
        # Prune if necessary
        self._prune_if_needed()
    
    def _prune_if_needed(self) -> None:
        """Prune old messages if limits exceeded."""
        # Keep system messages and recent messages
        if len(self.messages) > self.max_messages:
            # Find first non-system message to start pruning
            prune_idx = 0
            for i, msg in enumerate(self.messages):
                if msg.role != "system":
                    prune_idx = i
                    break
            
            # Keep last max_messages/2 messages
            keep_from = max(prune_idx, len(self.messages) - self.max_messages // 2)
            self.messages = self.messages[:1] + self.messages[keep_from:]
    
    def get_messages(self, include_system: bool = True) -> List[BedrockMessage]:
        """Get all messages, optionally excluding system messages."""
        if include_system:
            return self.messages
        return [m for m in self.messages if m.role != "system"]
    
    def to_claude_format(self) -> List[Dict[str, Any]]:
        """Convert all messages to Claude format."""
        return [m.to_claude_format() for m in self.messages]
    
    def clear(self) -> None:
        """Clear all messages except system messages."""
        system_messages = [m for m in self.messages if m.role == "system"]
        self.messages = system_messages
        self._token_count = sum(len(str(m.content)) // 4 for m in system_messages)
    
    def get_context_window(self, max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get the most recent messages within context window."""
        messages = self.messages
        if max_messages:
            messages = messages[-max_messages:]
        return [m.to_claude_format() for m in messages]


class BedrockClient:
    """
    Client for AWS Bedrock Claude API.
    
    Provides streaming responses, tool use, and conversation management.
    """
    
    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        self.model_id = model_id or settings.BEDROCK_MODEL_ID
        self.region = region or settings.AWS_REGION
        self.max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS
        self.temperature = temperature or settings.BEDROCK_TEMPERATURE
        
        # Initialize Bedrock client
        config = BotoConfig(
            region_name=self.region,
            retries={"max_attempts": 3, "mode": "adaptive"}
        )
        
        client_kwargs = {"config": config}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        
        self.client = boto3.client("bedrock-runtime", **client_kwargs)
        
        # Tool registry
        self._tools: Dict[str, BedrockTool] = {}
        
        # Conversation memories per session
        self._memories: Dict[str, ConversationMemory] = {}
    
    def register_tool(self, tool: BedrockTool) -> None:
        """Register a tool for function calling."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_or_create_memory(self, session_id: str) -> ConversationMemory:
        """Get or create conversation memory for a session."""
        if session_id not in self._memories:
            self._memories[session_id] = ConversationMemory()
        return self._memories[session_id]
    
    def clear_memory(self, session_id: str) -> None:
        """Clear conversation memory for a session."""
        if session_id in self._memories:
            self._memories[session_id].clear()
    
    async def generate(
        self,
        messages: List[BedrockMessage],
        tools: Optional[List[BedrockTool]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> BedrockResponse:
        """
        Generate a response from Claude.
        
        Args:
            messages: List of conversation messages
            tools: Optional tools for function calling
            system_prompt: Optional system prompt
            max_tokens: Override default max tokens
            temperature: Override default temperature
            session_id: Optional session ID for memory management
            
        Returns:
            BedrockResponse with content and metadata
        """
        # Build request body
        body: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "messages": [m.to_claude_format() for m in messages]
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        # Add tools if provided
        all_tools = list(self._tools.values())
        if tools:
            all_tools.extend(tools)
        
        if all_tools:
            body["tools"] = [t.to_claude_format() for t in all_tools]
            body["tool_choice"] = {"type": "auto"}
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract content
            content_parts = response_body.get("content", [])
            text_content = ""
            tool_calls = []
            
            for part in content_parts:
                if part.get("type") == "text":
                    text_content += part.get("text", "")
                elif part.get("type") == "tool_use":
                    tool_calls.append({
                        "id": part.get("id"),
                        "name": part.get("name"),
                        "input": part.get("input", {})
                    })
            
            # Update memory if session_id provided
            if session_id:
                memory = self.get_or_create_memory(session_id)
                for msg in messages:
                    memory.add_message(msg)
                memory.add_message(BedrockMessage.assistant(text_content))
            
            return BedrockResponse(
                content=text_content,
                stop_reason=response_body.get("stop_reason", "end_turn"),
                usage=response_body.get("usage", {}),
                tool_calls=tool_calls,
                raw_response=response_body
            )
            
        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            raise BedrockError(f"Failed to generate response: {e}") from e
    
    async def generate_stream(
        self,
        messages: List[BedrockMessage],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from Claude.
        
        Yields text chunks as they are generated.
        """
        body: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "messages": [m.to_claude_format() for m in messages]
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                
                if chunk.get("type") == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")
                        
        except Exception as e:
            logger.error(f"Bedrock streaming error: {e}")
            raise BedrockError(f"Failed to stream response: {e}") from e
    
    async def execute_with_tools(
        self,
        messages: List[BedrockMessage],
        system_prompt: Optional[str] = None,
        max_iterations: int = 5,
        session_id: Optional[str] = None
    ) -> BedrockResponse:
        """
        Generate response with automatic tool execution.
        
        Will continue calling tools and feeding results back to Claude
        until no more tool calls are requested or max_iterations reached.
        """
        current_messages = messages.copy()
        all_tool_results = []
        
        for iteration in range(max_iterations):
            response = await self.generate(
                messages=current_messages,
                system_prompt=system_prompt,
                session_id=session_id if iteration == 0 else None  # Only add to memory on first call
            )
            
            # If no tool calls, we're done
            if not response.tool_calls:
                return response
            
            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]
                tool_use_id = tool_call["id"]
                
                if tool_name in self._tools:
                    tool = self._tools[tool_name]
                    try:
                        if tool.handler:
                            result = await tool.handler(tool_input)
                        else:
                            result = {"error": f"Tool {tool_name} has no handler"}
                    except Exception as e:
                        result = {"error": str(e)}
                        logger.error(f"Tool execution error for {tool_name}: {e}")
                else:
                    result = {"error": f"Tool {tool_name} not found"}
                
                # Add tool result to messages
                current_messages.append(
                    BedrockMessage.tool_result(tool_use_id, result, is_error="error" in result)
                )
                all_tool_results.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": result
                })
        
        # Return final response after max iterations
        return await self.generate(
            messages=current_messages,
            system_prompt=system_prompt
        )
    
    async def quick_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Quick one-off generation without conversation history."""
        messages = [BedrockMessage.user(prompt)]
        response = await self.generate(
            messages=messages,
            system_prompt=system_prompt,
            session_id=session_id
        )
        return response.content


class BedrockError(Exception):
    """Error from Bedrock API."""
    pass


# Global client instance
_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    """Get or create global Bedrock client."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
