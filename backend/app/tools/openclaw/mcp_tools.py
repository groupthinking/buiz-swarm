"""
Flash Generator MCP Tools

MCP tool registration for the OpenClaw Flash Generator.
Allows agents to generate flash decks via the Model Context Protocol.
"""
from typing import Any, Dict, List
import logging

from ...core.mcp_client import mcp_client
from ...tools.openclaw.flash_generator import FlashGenerator, FlashCard
from ...tools.openclaw.business import BusinessTopics

logger = logging.getLogger(__name__)


async def list_flash_topics(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    List available flash card topics.

    Args:
        params: Empty or unused

    Returns:
        List of available topic names
    """
    try:
        topics = BusinessTopics.list_topics()
        return {
            "status": "success",
            "topics": topics,
            "count": len(topics)
        }
    except Exception as e:
        logger.error(f"Error listing topics: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


async def generate_flash_deck(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a flash deck for a specific topic.

    Args:
        params: {
            "topic": str - Topic name (finance, marketing, etc.),
            "shuffle": bool - Whether to shuffle cards (optional),
            "limit": int - Max cards to include (optional)
        }

    Returns:
        Flash deck with cards
    """
    try:
        topic = params.get("topic")
        if not topic:
            return {
                "status": "error",
                "error": "Missing required parameter: topic"
            }

        if topic not in BusinessTopics.list_topics():
            return {
                "status": "error",
                "error": f"Invalid topic: {topic}. Available: {BusinessTopics.list_topics()}"
            }

        shuffle = params.get("shuffle", False)
        limit = params.get("limit")

        generator = FlashGenerator()
        deck = generator.generate_from_topic(topic, shuffle=shuffle)

        cards_data = [card.to_dict() for card in deck.cards]
        if limit and limit > 0:
            cards_data = cards_data[:limit]

        return {
            "status": "success",
            "topic": topic,
            "cards": cards_data,
            "total_cards": len(cards_data)
        }

    except Exception as e:
        logger.error(f"Error generating deck: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


async def combine_flash_topics(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine multiple topics into a single flash deck.

    Args:
        params: {
            "topics": List[str] - List of topic names,
            "shuffle": bool - Whether to shuffle (optional)
        }

    Returns:
        Combined flash deck
    """
    try:
        topics = params.get("topics", [])
        if not topics:
            return {
                "status": "error",
                "error": "Missing required parameter: topics (list)"
            }

        available_topics = BusinessTopics.list_topics()
        invalid_topics = [t for t in topics if t not in available_topics]

        if invalid_topics:
            return {
                "status": "error",
                "error": f"Invalid topics: {invalid_topics}. Available: {available_topics}"
            }

        shuffle = params.get("shuffle", False)

        generator = FlashGenerator()
        deck = generator.combine_topics(topics, shuffle=shuffle)

        return {
            "status": "success",
            "topics": topics,
            "cards": [card.to_dict() for card in deck.cards],
            "total_cards": len(deck.cards)
        }

    except Exception as e:
        logger.error(f"Error combining topics: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def register_flash_tools():
    """Register flash generator tools with MCP client."""

    # Register list_topics tool
    mcp_client.register_tool(
        name="list_flash_topics",
        description="List available flash card topics for business learning",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        },
        handler=list_flash_topics
    )

    # Register generate_deck tool
    mcp_client.register_tool(
        name="generate_flash_deck",
        description="Generate a flash deck for a specific business topic (finance, marketing, strategy, leadership, operations, sales)",
        parameters={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic name (finance, marketing, strategy, leadership, operations, sales)",
                    "enum": BusinessTopics.list_topics()
                },
                "shuffle": {
                    "type": "boolean",
                    "description": "Whether to shuffle the cards",
                    "default": False
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of cards to include",
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["topic"]
        },
        handler=generate_flash_deck
    )

    # Register combine_topics tool
    mcp_client.register_tool(
        name="combine_flash_topics",
        description="Combine multiple business topics into a single flash deck",
        parameters={
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of topic names to combine"
                },
                "shuffle": {
                    "type": "boolean",
                    "description": "Whether to shuffle the combined deck",
                    "default": False
                }
            },
            "required": ["topics"]
        },
        handler=combine_flash_topics
    )

    logger.info("Flash generator MCP tools registered")
