"""OpenClaw Flash Generator — REST API (Flask).

Run with:
    python app.py
or:
    flask --app app run
"""

from __future__ import annotations

from flask import Flask, jsonify, request

from openclaw.flash_generator import FlashGenerator

app = Flask(__name__)
_gen = FlashGenerator()


# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #


@app.get("/topics")
def list_topics():
    """List all available built-in business topics."""
    return jsonify({"topics": _gen.list_topics()})


@app.get("/generate/<topic>")
def generate(topic: str):
    """Generate a flash deck for a built-in business *topic*.

    Query parameters:
        shuffle (bool): Shuffle the card order (default: false).
    """
    shuffle = request.args.get("shuffle", "false").lower() in ("1", "true", "yes")
    try:
        deck = _gen.generate(topic, shuffle=shuffle)
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify(deck.to_dict())


@app.post("/generate/custom")
def generate_custom():
    """Generate a flash deck from custom (front, back) pairs.

    Request body (JSON)::

        {
            "topic": "My Topic",
            "pairs": [
                {"front": "Q1", "back": "A1"},
                {"front": "Q2", "back": "A2"}
            ],
            "shuffle": false
        }
    """
    body = request.get_json(silent=True) or {}
    topic = body.get("topic", "Custom")
    raw_pairs = body.get("pairs", [])
    shuffle = bool(body.get("shuffle", False))

    if not isinstance(raw_pairs, list):
        return jsonify({"error": "'pairs' must be a list of {front, back} objects."}), 400

    pairs = []
    for item in raw_pairs:
        if not isinstance(item, dict) or "front" not in item or "back" not in item:
            return jsonify({"error": "Each pair must have 'front' and 'back' fields."}), 400
        pairs.append((str(item["front"]), str(item["back"])))

    deck = _gen.from_pairs(topic, pairs, shuffle=shuffle)
    return jsonify(deck.to_dict()), 201


@app.post("/combine")
def combine():
    """Combine multiple built-in topics into one deck.

    Request body (JSON)::

        {
            "topics": ["finance", "strategy"],
            "shuffle": false,
            "combined_topic": "Finance & Strategy"
        }
    """
    body = request.get_json(silent=True) or {}
    topics = body.get("topics", [])
    shuffle = bool(body.get("shuffle", False))
    combined_topic = body.get("combined_topic")

    if not isinstance(topics, list) or len(topics) == 0:
        return jsonify({"error": "'topics' must be a non-empty list of topic names."}), 400

    try:
        deck = _gen.combine(topics, shuffle=shuffle, combined_topic=combined_topic)
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(deck.to_dict()), 201


# ------------------------------------------------------------------ #
# Dev server                                                           #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    app.run(debug=False)
