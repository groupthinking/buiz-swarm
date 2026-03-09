"""
Flash Generator API Router

FastAPI routes for the OpenClaw Flash Generator.
Provides endpoints for generating business flash-card decks.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...tools.openclaw.flash_generator import FlashGenerator, FlashCard, FlashDeck
from ...tools.openclaw.business import BusinessTopics

router = APIRouter(prefix="/tools/flash", tags=["flash-generator"])


class FlashCardResponse(BaseModel):
    """Flash card response model."""
    front: str = Field(..., description="Front of the card (question/prompt)")
    back: str = Field(..., description="Back of the card (answer/content)")
    tags: List[str] = Field(default_factory=list, description="Topic tags")

    class Config:
        json_schema_extra = {
            "example": {
                "front": "What is ROI?",
                "back": "Return on Investment - measures gain relative to cost",
                "tags": ["finance"]
            }
        }


class FlashDeckResponse(BaseModel):
    """Flash deck response model."""
    topic: str = Field(..., description="Topic name")
    cards: List[FlashCardResponse] = Field(..., description="List of flash cards")
    total_cards: int = Field(..., description="Total number of cards")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "finance",
                "total_cards": 5,
                "cards": []
            }
        }


class CustomCardRequest(BaseModel):
    """Request model for custom card generation."""
    front: str = Field(..., description="Front content")
    back: str = Field(..., description="Back content")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags")


class CustomDeckRequest(BaseModel):
    """Request model for custom deck generation."""
    cards: List[CustomCardRequest] = Field(..., description="Custom cards")
    shuffle: bool = Field(default=False, description="Shuffle the deck")


class CombineTopicsRequest(BaseModel):
    """Request model for combining multiple topics."""
    topics: List[str] = Field(..., description="List of topics to combine")
    shuffle: bool = Field(default=False, description="Shuffle the combined deck")


@router.get("/topics", response_model=List[str])
async def list_topics() -> List[str]:
    """
    List all available built-in topics.

    Returns:
        List of available topic names (finance, marketing, strategy, etc.)
    """
    return BusinessTopics.list_topics()


@router.get("/generate/{topic}", response_model=FlashDeckResponse)
async def generate_deck(
    topic: str,
    shuffle: bool = Query(default=False, description="Shuffle the deck"),
    limit: Optional[int] = Query(default=None, description="Limit number of cards")
) -> FlashDeckResponse:
    """
    Generate a flash deck for a specific topic.

    Args:
        topic: Topic name (use /topics to see available options)
        shuffle: Whether to shuffle the cards
        limit: Maximum number of cards to include

    Returns:
        FlashDeck with cards for the requested topic

    Raises:
        HTTPException: If topic is not found
    """
    if topic not in BusinessTopics.list_topics():
        raise HTTPException(
            status_code=404,
            detail=f"Topic '{topic}' not found. Available: {BusinessTopics.list_topics()}"
        )

    generator = FlashGenerator()
    deck = generator.generate_from_topic(topic, shuffle=shuffle)

    if limit and limit > 0:
        deck.cards = deck.cards[:limit]

    return FlashDeckResponse(
        topic=topic,
        cards=[FlashCardResponse(**card.to_dict()) for card in deck.cards],
        total_cards=len(deck.cards)
    )


@router.post("/generate/custom", response_model=FlashDeckResponse)
async def generate_custom_deck(request: CustomDeckRequest) -> FlashDeckResponse:
    """
    Generate a custom flash deck from provided cards.

    Args:
        request: Custom deck request with cards

    Returns:
        FlashDeck with custom cards
    """
    generator = FlashGenerator()

    cards = [
        FlashCard(
            front=card.front,
            back=card.back,
            tags=card.tags or []
        )
        for card in request.cards
    ]

    deck = generator.generate_from_cards(cards, shuffle=request.shuffle)

    return FlashDeckResponse(
        topic="custom",
        cards=[FlashCardResponse(**card.to_dict()) for card in deck.cards],
        total_cards=len(deck.cards)
    )


@router.post("/combine", response_model=FlashDeckResponse)
async def combine_topics(request: CombineTopicsRequest) -> FlashDeckResponse:
    """
    Combine multiple topics into a single flash deck.

    Args:
        request: Combine request with topics list

    Returns:
        Combined FlashDeck with all topic cards

    Raises:
        HTTPException: If any topic is not found
    """
    # Validate all topics exist
    available_topics = BusinessTopics.list_topics()
    invalid_topics = [t for t in request.topics if t not in available_topics]

    if invalid_topics:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid topics: {invalid_topics}. Available: {available_topics}"
        )

    generator = FlashGenerator()
    deck = generator.combine_topics(request.topics, shuffle=request.shuffle)

    return FlashDeckResponse(
        topic=f"combined: {', '.join(request.topics)}",
        cards=[FlashCardResponse(**card.to_dict()) for card in deck.cards],
        total_cards=len(deck.cards)
    )
