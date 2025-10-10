"""Transaction data parser for extracting information from UI elements."""

import re
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class Transaction:
    """Represents a single transaction."""

    date: str
    description: str
    amount: Decimal
    currency: str
    category: Optional[str] = None
    foreign_amount: Optional[str] = None

    def __hash__(self):
        """Make transaction hashable for duplicate detection."""
        return hash((self.date, self.description, str(self.amount), self.currency))

    def is_spending(self) -> bool:
        """Check if transaction is a spending (negative amount)."""
        return self.amount < 0


class TransactionParser:
    """Parses transaction data from UI elements."""

    def __init__(self, current_date_header: str = ""):
        """
        Initialize parser.

        Args:
            current_date_header: The current date section being processed (e.g., "SUN, 5 OCTOBER")
        """
        self.current_date = current_date_header

    def parse_transaction(self, element_text: str) -> Optional[Transaction]:
        """
        Parse a transaction from element text.

        Expected format (multi-line in label attribute):
        "Bowlito
        Restaurant
        -47.24 AED
        -415.00 THB"

        Or:
        "Illia Pivtoraiko to Temp
        -151,000.00 AED"

        Args:
            element_text: The text content from XCUIElementTypeStaticText

        Returns:
            Transaction object if valid spending, None otherwise
        """
        if not element_text or "AED" not in element_text:
            return None

        lines = [line.strip() for line in element_text.split("\n") if line.strip()]

        if len(lines) < 2:
            return None

        # Find the AED amount line
        aed_amount = None
        foreign_amount = None
        description_lines = []
        category = None

        for i, line in enumerate(lines):
            if "AED" in line:
                # This is the primary amount line
                aed_amount = self._extract_amount(line)
                # Check if there's a foreign currency line after
                if i + 1 < len(lines) and ("THB" in lines[i + 1] or "USD" in lines[i + 1]):
                    foreign_amount = lines[i + 1]
                # Everything before this line is description/category
                description_lines = lines[:i]
                break

        if aed_amount is None:
            return None

        # Parse description and category
        # First line is usually merchant/description
        # Second line (if exists and not amount) is usually category
        description = description_lines[0] if description_lines else "Unknown"

        if len(description_lines) > 1:
            # Check if second line looks like a category (single word, capitalized)
            potential_category = description_lines[1]
            if potential_category and not re.search(r'\d', potential_category):
                category = potential_category
                # For transfers or other multi-word descriptions, keep full description
                if len(description_lines) == 2:
                    # Simple case: merchant + category
                    pass
                else:
                    # Complex case: might be multi-line description
                    description = " ".join(description_lines[:-1]) if category else description

        return Transaction(
            date=self.current_date,
            description=description,
            amount=aed_amount,
            currency="AED",
            category=category,
            foreign_amount=foreign_amount,
        )

    @staticmethod
    def _extract_amount(amount_str: str) -> Optional[Decimal]:
        """
        Extract decimal amount from string like '-47.24 AED' or '-151,000.00 AED'.

        Args:
            amount_str: String containing amount and currency

        Returns:
            Decimal value or None if parsing fails
        """
        # Remove currency and whitespace
        cleaned = amount_str.replace("AED", "").replace(",", "").strip()

        # Extract number (including negative sign and decimal point)
        match = re.search(r'[+-]?\d+\.?\d*', cleaned)
        if match:
            try:
                return Decimal(match.group())
            except:
                return None

        return None

    def update_current_date(self, date_header: str):
        """
        Update the current date being processed.

        Args:
            date_header: Date header text (e.g., "SUN, 5 OCTOBER")
        """
        self.current_date = date_header
