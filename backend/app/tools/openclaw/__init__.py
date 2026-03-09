"""OpenClaw Flash Generator — built-in business flash-card toolkit."""

from openclaw.flash_generator import FlashCard, FlashDeck, FlashGenerator
from openclaw.business import BusinessTopics

__all__ = ["FlashCard", "FlashDeck", "FlashGenerator", "BusinessTopics"]
__version__ = "0.1.0"


# MCP tool registration
from .mcp_tools import register_flash_tools

__all__ = [
    "FlashCard",
    "FlashDeck", 
    "FlashGenerator",
    "BusinessTopics",
    "register_flash_tools"
]
