"""Core flash-card models and FlashGenerator for OpenClaw."""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple


# ------------------------------------------------------------------ #
# Data models                                                          #
# ------------------------------------------------------------------ #


@dataclass
class FlashCard:
    """A single flash card with a *front* (question/term) and *back* (answer).

    Args:
        front: The question or term shown on the card's front face.
        back: The answer or definition shown on the card's back face.
        card_id: Optional unique identifier; auto-generated if not provided.
        tags: Optional list of tags for filtering.
    """

    front: str
    back: str
    card_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tags: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict:
        """Serialise the card to a plain dictionary."""
        return {
            "card_id": self.card_id,
            "front": self.front,
            "back": self.back,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FlashCard":
        """Deserialise a card from a plain dictionary."""
        return cls(
            front=data["front"],
            back=data["back"],
            card_id=data.get("card_id", str(uuid.uuid4())),
            tags=data.get("tags", []),
        )

    def __repr__(self) -> str:
        return f"FlashCard(front={self.front!r})"


@dataclass
class FlashDeck:
    """An ordered collection of :class:`FlashCard` objects for a given topic.

    Args:
        topic: Human-readable name for the deck's subject matter.
        cards: Initial list of flash cards.
        deck_id: Optional unique identifier; auto-generated if not provided.
    """

    topic: str
    cards: List[FlashCard] = field(default_factory=list)
    deck_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_card(self, front: str, back: str, tags: Optional[List[str]] = None) -> FlashCard:
        """Create and append a new :class:`FlashCard` to this deck.

        Returns the newly created card.
        """
        card = FlashCard(front=front, back=back, tags=tags or [])
        self.cards.append(card)
        return card

    def remove_card(self, card_id: str) -> bool:
        """Remove the card with *card_id*. Returns True if removed, False if not found."""
        before = len(self.cards)
        self.cards = [c for c in self.cards if c.card_id != card_id]
        return len(self.cards) < before

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.cards)

    def __iter__(self) -> Iterator[FlashCard]:
        return iter(self.cards)

    def __repr__(self) -> str:
        return f"FlashDeck(topic={self.topic!r}, cards={len(self.cards)})"

    def shuffled(self) -> List[FlashCard]:
        """Return a shuffled copy of the card list (does not mutate the deck)."""
        cards = list(self.cards)
        random.shuffle(cards)
        return cards

    def filter_by_tag(self, tag: str) -> List[FlashCard]:
        """Return cards that contain *tag*."""
        return [c for c in self.cards if tag in c.tags]

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict:
        """Serialise the deck to a plain dictionary."""
        return {
            "deck_id": self.deck_id,
            "topic": self.topic,
            "cards": [c.to_dict() for c in self.cards],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialise the deck to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict) -> "FlashDeck":
        """Deserialise a deck from a plain dictionary."""
        cards = [FlashCard.from_dict(c) for c in data.get("cards", [])]
        return cls(
            topic=data["topic"],
            cards=cards,
            deck_id=data.get("deck_id", str(uuid.uuid4())),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "FlashDeck":
        """Deserialise a deck from a JSON string."""
        return cls.from_dict(json.loads(json_str))


# ------------------------------------------------------------------ #
# Generator                                                            #
# ------------------------------------------------------------------ #


class FlashGenerator:
    """Generates :class:`FlashDeck` objects for business topics instantly.

    Usage::

        gen = FlashGenerator()

        # Generate a deck from a built-in business topic
        deck = gen.generate("marketing")

        # Generate a deck from custom (front, back) pairs
        deck = gen.from_pairs("My Topic", [("Q1", "A1"), ("Q2", "A2")])

        # Generate a combined deck from multiple topics
        deck = gen.combine(["finance", "strategy"])
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialise the generator.

        Args:
            seed: Optional random seed for reproducible shuffling.
        """
        if seed is not None:
            random.seed(seed)
        # Import here to avoid circular dependency
        from openclaw.business import BusinessTopics
        self._business = BusinessTopics

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, topic: str, *, shuffle: bool = False, tags: Optional[List[str]] = None) -> FlashDeck:
        """Generate a :class:`FlashDeck` for a built-in business *topic*.

        Args:
            topic: The business topic name (case-insensitive).
            shuffle: If True, randomise card order.
            tags: Optional tags applied to every generated card.

        Returns:
            A populated :class:`FlashDeck`.

        Raises:
            KeyError: If the topic is not found in the built-in catalogue.
        """
        pairs: List[Tuple[str, str]] = self._business.get_cards(topic)
        deck = self.from_pairs(topic.title(), pairs, shuffle=shuffle, tags=tags)
        return deck

    def from_pairs(
        self,
        topic: str,
        pairs: List[Tuple[str, str]],
        *,
        shuffle: bool = False,
        tags: Optional[List[str]] = None,
    ) -> FlashDeck:
        """Build a :class:`FlashDeck` from arbitrary (front, back) *pairs*.

        Args:
            topic: Human-readable name for the deck.
            pairs: Iterable of (front, back) string tuples.
            shuffle: If True, randomise card order.
            tags: Optional tags applied to every card.

        Returns:
            A populated :class:`FlashDeck`.
        """
        deck = FlashDeck(topic=topic)
        card_tags = list(tags) if tags else []
        items: List[Tuple[str, str]] = list(pairs)
        if shuffle:
            random.shuffle(items)
        for front, back in items:
            deck.add_card(front, back, tags=card_tags)
        return deck

    def combine(
        self,
        topics: List[str],
        *,
        shuffle: bool = False,
        combined_topic: Optional[str] = None,
    ) -> FlashDeck:
        """Combine multiple built-in topics into a single :class:`FlashDeck`.

        Args:
            topics: List of built-in topic names.
            shuffle: If True, randomise card order in the combined deck.
            combined_topic: Override the deck's topic name.

        Returns:
            A merged :class:`FlashDeck`.
        """
        all_pairs: List[Tuple[str, str]] = []
        for t in topics:
            all_pairs.extend(self._business.get_cards(t))
        name = combined_topic or " & ".join(t.title() for t in topics)
        return self.from_pairs(name, all_pairs, shuffle=shuffle)

    def list_topics(self) -> List[str]:
        """Return the names of all available built-in business topics."""
        return self._business.list_topics()
