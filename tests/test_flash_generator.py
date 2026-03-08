"""Tests for the OpenClaw Flash Generator."""

from __future__ import annotations

import json
import pytest

from openclaw.business import BusinessTopics
from openclaw.flash_generator import FlashCard, FlashDeck, FlashGenerator


# ------------------------------------------------------------------ #
# FlashCard                                                            #
# ------------------------------------------------------------------ #


class TestFlashCard:
    def test_creation_defaults(self):
        card = FlashCard(front="What is ROI?", back="Return on Investment.")
        assert card.front == "What is ROI?"
        assert card.back == "Return on Investment."
        assert card.card_id  # auto-generated UUID
        assert card.tags == []

    def test_creation_with_tags(self):
        card = FlashCard(front="Q", back="A", tags=["finance", "basics"])
        assert card.tags == ["finance", "basics"]

    def test_unique_ids(self):
        c1 = FlashCard(front="Q", back="A")
        c2 = FlashCard(front="Q", back="A")
        assert c1.card_id != c2.card_id

    def test_to_dict(self):
        card = FlashCard(front="Q", back="A", card_id="abc-123", tags=["t1"])
        d = card.to_dict()
        assert d == {"card_id": "abc-123", "front": "Q", "back": "A", "tags": ["t1"]}

    def test_from_dict_round_trip(self):
        card = FlashCard(front="Q", back="A", tags=["x"])
        restored = FlashCard.from_dict(card.to_dict())
        assert restored.front == card.front
        assert restored.back == card.back
        assert restored.card_id == card.card_id
        assert restored.tags == card.tags

    def test_from_dict_generates_id_if_missing(self):
        card = FlashCard.from_dict({"front": "Q", "back": "A"})
        assert card.card_id  # should generate one


# ------------------------------------------------------------------ #
# FlashDeck                                                            #
# ------------------------------------------------------------------ #


class TestFlashDeck:
    def test_empty_deck(self):
        deck = FlashDeck(topic="Test")
        assert deck.topic == "Test"
        assert len(deck) == 0

    def test_add_card(self):
        deck = FlashDeck(topic="Test")
        card = deck.add_card("Q1", "A1")
        assert len(deck) == 1
        assert card.front == "Q1"

    def test_add_multiple_cards(self):
        deck = FlashDeck(topic="Test")
        deck.add_card("Q1", "A1")
        deck.add_card("Q2", "A2")
        assert len(deck) == 2

    def test_remove_card(self):
        deck = FlashDeck(topic="Test")
        card = deck.add_card("Q1", "A1")
        removed = deck.remove_card(card.card_id)
        assert removed is True
        assert len(deck) == 0

    def test_remove_nonexistent_card(self):
        deck = FlashDeck(topic="Test")
        removed = deck.remove_card("nonexistent-id")
        assert removed is False

    def test_iteration(self):
        deck = FlashDeck(topic="Test")
        deck.add_card("Q1", "A1")
        deck.add_card("Q2", "A2")
        fronts = [c.front for c in deck]
        assert fronts == ["Q1", "Q2"]

    def test_shuffled_returns_all_cards(self):
        deck = FlashDeck(topic="Test")
        for i in range(10):
            deck.add_card(f"Q{i}", f"A{i}")
        shuffled = deck.shuffled()
        assert len(shuffled) == 10
        assert set(c.front for c in shuffled) == {f"Q{i}" for i in range(10)}

    def test_shuffled_does_not_mutate_deck(self):
        deck = FlashDeck(topic="Test")
        deck.add_card("Q1", "A1")
        deck.add_card("Q2", "A2")
        _ = deck.shuffled()
        assert [c.front for c in deck] == ["Q1", "Q2"]

    def test_filter_by_tag(self):
        deck = FlashDeck(topic="Test")
        deck.add_card("Q1", "A1", tags=["finance"])
        deck.add_card("Q2", "A2", tags=["marketing"])
        deck.add_card("Q3", "A3", tags=["finance"])
        finance_cards = deck.filter_by_tag("finance")
        assert len(finance_cards) == 2
        assert all("finance" in c.tags for c in finance_cards)

    def test_to_dict_structure(self):
        deck = FlashDeck(topic="Test", deck_id="deck-001")
        deck.add_card("Q1", "A1")
        d = deck.to_dict()
        assert d["deck_id"] == "deck-001"
        assert d["topic"] == "Test"
        assert len(d["cards"]) == 1

    def test_to_json_valid(self):
        deck = FlashDeck(topic="JSON Test")
        deck.add_card("Q1", "A1")
        raw = deck.to_json()
        parsed = json.loads(raw)
        assert parsed["topic"] == "JSON Test"

    def test_from_dict_round_trip(self):
        deck = FlashDeck(topic="Round Trip", deck_id="d-1")
        deck.add_card("Q1", "A1", tags=["t"])
        restored = FlashDeck.from_dict(deck.to_dict())
        assert restored.topic == deck.topic
        assert restored.deck_id == deck.deck_id
        assert len(restored) == 1

    def test_from_json_round_trip(self):
        deck = FlashDeck(topic="JSON Round Trip")
        deck.add_card("Q1", "A1")
        restored = FlashDeck.from_json(deck.to_json())
        assert restored.topic == deck.topic
        assert len(restored) == 1


# ------------------------------------------------------------------ #
# BusinessTopics                                                       #
# ------------------------------------------------------------------ #


class TestBusinessTopics:
    def test_list_topics_returns_sorted(self):
        topics = BusinessTopics.list_topics()
        assert topics == sorted(topics)
        assert len(topics) > 0

    def test_all_builtin_topics_present(self):
        topics = BusinessTopics.list_topics()
        for expected in ["finance", "marketing", "operations", "sales", "strategy", "leadership"]:
            assert expected in topics

    def test_get_cards_returns_pairs(self):
        cards = BusinessTopics.get_cards("finance")
        assert isinstance(cards, list)
        assert len(cards) > 0
        for front, back in cards:
            assert isinstance(front, str) and front
            assert isinstance(back, str) and back

    def test_get_cards_case_insensitive(self):
        lower = BusinessTopics.get_cards("finance")
        upper = BusinessTopics.get_cards("FINANCE")
        mixed = BusinessTopics.get_cards("Finance")
        assert lower == upper == mixed

    def test_get_cards_unknown_topic_raises(self):
        with pytest.raises(KeyError, match="Unknown topic"):
            BusinessTopics.get_cards("nonexistent_topic_xyz")

    def test_is_valid_topic(self):
        assert BusinessTopics.is_valid_topic("marketing") is True
        assert BusinessTopics.is_valid_topic("MARKETING") is True
        assert BusinessTopics.is_valid_topic("bogus") is False


# ------------------------------------------------------------------ #
# FlashGenerator                                                       #
# ------------------------------------------------------------------ #


class TestFlashGenerator:
    @pytest.fixture
    def gen(self):
        return FlashGenerator(seed=42)

    def test_list_topics(self, gen):
        topics = gen.list_topics()
        assert "marketing" in topics
        assert "finance" in topics

    def test_generate_returns_deck(self, gen):
        deck = gen.generate("marketing")
        assert isinstance(deck, FlashDeck)
        assert len(deck) > 0

    def test_generate_topic_title_case(self, gen):
        deck = gen.generate("finance")
        assert deck.topic == "Finance"

    def test_generate_unknown_topic_raises(self, gen):
        with pytest.raises(KeyError):
            gen.generate("unknown_topic_xyz")

    def test_generate_shuffle(self, gen):
        # Seeded generator — shuffled deck has same cards but may differ in order
        deck_normal = gen.generate("operations", shuffle=False)
        deck_shuffled = gen.generate("operations", shuffle=True)
        assert len(deck_normal) == len(deck_shuffled)
        assert {c.front for c in deck_normal} == {c.front for c in deck_shuffled}

    def test_generate_with_tags(self, gen):
        deck = gen.generate("sales", tags=["auto-tagged"])
        for card in deck:
            assert "auto-tagged" in card.tags

    def test_from_pairs(self, gen):
        pairs = [("What is X?", "X is ..."), ("What is Y?", "Y is ...")]
        deck = gen.from_pairs("Custom", pairs)
        assert deck.topic == "Custom"
        assert len(deck) == 2
        assert deck.cards[0].front == "What is X?"

    def test_from_pairs_shuffle(self, gen):
        pairs = [(f"Q{i}", f"A{i}") for i in range(10)]
        deck = gen.from_pairs("Shuffled", pairs, shuffle=True)
        assert len(deck) == 10
        assert {c.front for c in deck} == {f"Q{i}" for i in range(10)}

    def test_from_pairs_empty(self, gen):
        deck = gen.from_pairs("Empty", [])
        assert len(deck) == 0

    def test_combine(self, gen):
        deck = gen.combine(["finance", "marketing"])
        fin_cards = len(BusinessTopics.get_cards("finance"))
        mkt_cards = len(BusinessTopics.get_cards("marketing"))
        assert len(deck) == fin_cards + mkt_cards

    def test_combine_topic_name(self, gen):
        deck = gen.combine(["finance", "strategy"])
        assert "Finance" in deck.topic
        assert "Strategy" in deck.topic

    def test_combine_custom_topic_name(self, gen):
        deck = gen.combine(["finance", "strategy"], combined_topic="FinStrat")
        assert deck.topic == "FinStrat"

    def test_combine_unknown_topic_raises(self, gen):
        with pytest.raises(KeyError):
            gen.combine(["finance", "unknown_xyz"])


# ------------------------------------------------------------------ #
# Flask API                                                            #
# ------------------------------------------------------------------ #


@pytest.fixture
def client():
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


class TestFlaskAPI:
    def test_list_topics(self, client):
        resp = client.get("/topics")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "topics" in data
        assert "finance" in data["topics"]

    def test_generate_valid_topic(self, client):
        resp = client.get("/generate/marketing")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["topic"] == "Marketing"
        assert len(data["cards"]) > 0

    def test_generate_unknown_topic(self, client):
        resp = client.get("/generate/nonexistent_xyz")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data

    def test_generate_shuffle_param(self, client):
        resp = client.get("/generate/finance?shuffle=true")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["cards"]) > 0

    def test_generate_custom_valid(self, client):
        payload = {
            "topic": "Test",
            "pairs": [{"front": "Q1", "back": "A1"}],
        }
        resp = client.post("/generate/custom", json=payload)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["topic"] == "Test"
        assert len(data["cards"]) == 1

    def test_generate_custom_invalid_pairs(self, client):
        payload = {"topic": "Bad", "pairs": "not-a-list"}
        resp = client.post("/generate/custom", json=payload)
        assert resp.status_code == 400

    def test_generate_custom_missing_back(self, client):
        payload = {"topic": "Bad", "pairs": [{"front": "Q1"}]}
        resp = client.post("/generate/custom", json=payload)
        assert resp.status_code == 400

    def test_combine_valid(self, client):
        payload = {"topics": ["finance", "sales"]}
        resp = client.post("/combine", json=payload)
        assert resp.status_code == 201
        data = resp.get_json()
        expected_count = (
            len(BusinessTopics.get_cards("finance"))
            + len(BusinessTopics.get_cards("sales"))
        )
        assert len(data["cards"]) == expected_count

    def test_combine_empty_topics(self, client):
        payload = {"topics": []}
        resp = client.post("/combine", json=payload)
        assert resp.status_code == 400

    def test_combine_unknown_topic(self, client):
        payload = {"topics": ["finance", "bogus_xyz"]}
        resp = client.post("/combine", json=payload)
        assert resp.status_code == 404
