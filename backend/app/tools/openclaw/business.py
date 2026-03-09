"""Built-in business topics and flash-card templates for OpenClaw."""

from __future__ import annotations

from typing import Dict, List, Tuple


class BusinessTopics:
    """Registry of built-in business topics with pre-defined flash-card data.

    Each topic maps to a list of (front, back) tuples that the FlashGenerator
    uses to produce ready-made FlashDeck objects.
    """

    # ------------------------------------------------------------------ #
    # Built-in topic catalogue                                             #
    # ------------------------------------------------------------------ #

    _BUILTIN: Dict[str, List[Tuple[str, str]]] = {
        "marketing": [
            ("What is a value proposition?",
             "A clear statement that explains how a product solves a problem, "
             "delivers benefits, and why customers should choose it over competitors."),
            ("What is a conversion rate?",
             "The percentage of visitors or prospects who complete a desired action "
             "(e.g., purchase, sign-up) out of total visitors."),
            ("What does CAC stand for?",
             "Customer Acquisition Cost — the total cost of acquiring a new customer, "
             "including marketing and sales expenses."),
            ("What is a USP?",
             "Unique Selling Proposition — the distinctive benefit that makes a product "
             "or service stand out from the competition."),
            ("What is A/B testing?",
             "A method of comparing two versions of a webpage, email, or asset to "
             "determine which one performs better."),
        ],
        "finance": [
            ("What is EBITDA?",
             "Earnings Before Interest, Taxes, Depreciation, and Amortization — a "
             "measure of a company's core operational profitability."),
            ("What is a P&L statement?",
             "Profit and Loss statement — a financial report summarising revenues, "
             "costs, and expenses over a specific period."),
            ("What is working capital?",
             "Current assets minus current liabilities — the funds available for "
             "day-to-day operations."),
            ("What is ROI?",
             "Return on Investment — a performance measure used to evaluate the "
             "efficiency of an investment: (gain – cost) / cost × 100 %."),
            ("What is a cash-flow statement?",
             "A financial statement showing the inflows and outflows of cash over "
             "a given period, split into operating, investing, and financing activities."),
        ],
        "strategy": [
            ("What is a SWOT analysis?",
             "A framework for evaluating Strengths, Weaknesses, Opportunities, and "
             "Threats facing a business or project."),
            ("What is Porter's Five Forces?",
             "A model analysing competitive forces: rivalry, threat of new entrants, "
             "threat of substitutes, buyer power, and supplier power."),
            ("What is a KPI?",
             "Key Performance Indicator — a measurable value that demonstrates how "
             "effectively an organisation is achieving a key business objective."),
            ("What is the BCG Matrix?",
             "A portfolio-management tool that categorises products into Stars, Cash "
             "Cows, Question Marks, and Dogs based on market growth and share."),
            ("What is a Blue Ocean Strategy?",
             "Creating uncontested market space by making the competition irrelevant, "
             "rather than competing in existing (red ocean) markets."),
        ],
        "leadership": [
            ("What is servant leadership?",
             "A leadership philosophy in which the leader's primary goal is to serve "
             "others — empowering and developing people rather than accumulating power."),
            ("What is emotional intelligence (EQ)?",
             "The ability to recognise, understand, and manage one's own emotions, "
             "and to recognise and influence the emotions of others."),
            ("What is transformational leadership?",
             "A style where a leader inspires and motivates followers to exceed "
             "expectations through vision, enthusiasm, and personal example."),
            ("What is the SMART goal framework?",
             "Goals that are Specific, Measurable, Achievable, Relevant, and "
             "Time-bound."),
            ("What is psychological safety?",
             "A shared belief that team members will not be punished or humiliated "
             "for speaking up with ideas, questions, concerns, or mistakes."),
        ],
        "operations": [
            ("What is Lean manufacturing?",
             "A production philosophy focused on eliminating waste (muda) while "
             "delivering maximum value to the customer."),
            ("What is Six Sigma?",
             "A data-driven methodology for eliminating defects and reducing "
             "variability in processes, aiming for 3.4 defects per million opportunities."),
            ("What is supply chain management (SCM)?",
             "The oversight of materials, information, and finances as they move "
             "from supplier to manufacturer to wholesaler to retailer to consumer."),
            ("What is OKR?",
             "Objectives and Key Results — a goal-setting framework where high-level "
             "objectives are paired with 2–5 measurable key results."),
            ("What is just-in-time (JIT) inventory?",
             "A strategy that aligns raw-material orders with production schedules "
             "to reduce inventory costs by receiving goods only as they are needed."),
        ],
        "sales": [
            ("What is the sales funnel?",
             "A model representing the stages a prospect goes through: Awareness → "
             "Interest → Decision → Action."),
            ("What is consultative selling?",
             "A sales approach focused on understanding the customer's needs and "
             "offering tailored solutions rather than pushing a product."),
            ("What is churn rate?",
             "The percentage of customers who stop using a product or service over "
             "a given time period: (lost customers / start-of-period customers) × 100 %."),
            ("What is CLV (Customer Lifetime Value)?",
             "The total revenue a business can expect from a single customer account "
             "throughout the business relationship."),
            ("What is upselling?",
             "Encouraging a customer to purchase a more expensive or upgraded version "
             "of the chosen item to increase the sale value."),
        ],
    }

    # ------------------------------------------------------------------ #
    # Public helpers                                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def list_topics(cls) -> List[str]:
        """Return the names of all built-in business topics."""
        return sorted(cls._BUILTIN.keys())

    @classmethod
    def get_cards(cls, topic: str) -> List[Tuple[str, str]]:
        """Return the (front, back) pairs for *topic*.

        Args:
            topic: A topic name (case-insensitive).

        Returns:
            List of (front, back) tuples.

        Raises:
            KeyError: If the topic is not found.
        """
        key = topic.lower()
        if key not in cls._BUILTIN:
            available = ", ".join(cls.list_topics())
            raise KeyError(
                f"Unknown topic '{topic}'. Available topics: {available}"
            )
        return list(cls._BUILTIN[key])

    @classmethod
    def is_valid_topic(cls, topic: str) -> bool:
        """Return True if *topic* is a known built-in topic."""
        return topic.lower() in cls._BUILTIN

