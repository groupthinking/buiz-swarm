"""Command-line interface for the OpenClaw Flash Generator."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from openclaw.flash_generator import FlashDeck, FlashGenerator


# ------------------------------------------------------------------ #
# Formatting helpers                                                   #
# ------------------------------------------------------------------ #


def _print_deck(deck: FlashDeck, *, show_answers: bool = False) -> None:
    """Pretty-print a :class:`FlashDeck` to stdout."""
    print(f"\n{'=' * 60}")
    print(f"  Deck : {deck.topic}")
    print(f"  Cards: {len(deck)}")
    print(f"{'=' * 60}")
    for i, card in enumerate(deck, start=1):
        print(f"\n[{i}] {card.front}")
        if show_answers:
            print(f"    → {card.back}")
    print()


# ------------------------------------------------------------------ #
# Argument parser                                                      #
# ------------------------------------------------------------------ #


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openclaw",
        description="OpenClaw Flash Generator — business flash cards for any instant.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── list ──────────────────────────────────────────────────────────
    sub.add_parser("list", help="List all available built-in business topics.")

    # ── generate ──────────────────────────────────────────────────────
    gen_p = sub.add_parser("generate", help="Generate a flash deck for a business topic.")
    gen_p.add_argument("topic", help="Built-in business topic (e.g. marketing, finance).")
    gen_p.add_argument(
        "--shuffle", action="store_true", help="Shuffle the card order."
    )
    gen_p.add_argument(
        "--answers", action="store_true", help="Show answers (card backs)."
    )
    gen_p.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output the deck as JSON instead of formatted text.",
    )

    # ── combine ───────────────────────────────────────────────────────
    comb_p = sub.add_parser("combine", help="Combine multiple topics into one deck.")
    comb_p.add_argument("topics", nargs="+", help="Built-in topic names to combine.")
    comb_p.add_argument("--shuffle", action="store_true", help="Shuffle the card order.")
    comb_p.add_argument("--answers", action="store_true", help="Show answers (card backs).")
    comb_p.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output the deck as JSON instead of formatted text.",
    )

    return parser


# ------------------------------------------------------------------ #
# Command handlers                                                     #
# ------------------------------------------------------------------ #


def _cmd_list(gen: FlashGenerator) -> None:
    topics = gen.list_topics()
    print("\nAvailable built-in business topics:\n")
    for t in topics:
        print(f"  • {t}")
    print()


def _cmd_generate(gen: FlashGenerator, args: argparse.Namespace) -> None:
    try:
        deck = gen.generate(args.topic, shuffle=args.shuffle)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    if args.as_json:
        print(deck.to_json())
    else:
        _print_deck(deck, show_answers=args.answers)


def _cmd_combine(gen: FlashGenerator, args: argparse.Namespace) -> None:
    try:
        deck = gen.combine(args.topics, shuffle=args.shuffle)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    if args.as_json:
        print(deck.to_json())
    else:
        _print_deck(deck, show_answers=args.answers)


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point for the OpenClaw Flash Generator."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    gen = FlashGenerator()

    if args.command == "list":
        _cmd_list(gen)
    elif args.command == "generate":
        _cmd_generate(gen, args)
    elif args.command == "combine":
        _cmd_combine(gen, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
